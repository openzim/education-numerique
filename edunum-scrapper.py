#!/usr/bin/env python3

""" E&N dump to zimwriterfs script

converts raw E&N folder (from OF) into a zimwriterfs friendly one. """

import os
import json
import shutil
import zipfile
import hashlib
import logging
import argparse
import subprocess

logging.basicConfig(format="%(levelname)s:%(message)s")
logger = logging.getLogger("edunum-scrapper")


def get_content_of(fpath):
    with open(fpath, "r") as fp:
        return fp.read()


def save_content_to(content, fpath):
    with open(fpath, "w") as fp:
        fp.write(content)


def download_kiwix_tools(working_dir):
    """ downloading image optimization scripts from kiwix/tools repo """
    tools_fpath = os.path.join(working_dir, "dumping_tools")
    if os.path.exists(tools_fpath):
        return

    commit = "bf10817cf9b207139443d95707855fc9c30659dc"
    inner_dir = f"tools-{commit}"
    tools_fpath = download_file(
        working_dir,
        f"https://github.com/kiwix/tools/archive/{commit}.zip",
        "tools.zip",
        "2c244e17b8a3275e756e2b2435c582c7",
    )

    with zipfile.ZipFile(tools_fpath, "r") as zip_archive:
        zip_archive.extractall(working_dir)

    # move the subfolder we're interested in
    shutil.move(
        os.path.join(working_dir, inner_dir, "dumping_tools"),
        os.path.join(working_dir, "dumping_tools"),
    )

    # remove zip leftovers
    shutil.rmtree(os.path.join(working_dir, inner_dir))

    # create log placeholder
    log_dir = os.path.join(working_dir, "dumping_tools", "log")
    os.makedirs(log_dir, exist_ok=True)
    save_content_to("", os.path.join(log_dir, "all.log"))


def optimize_content(working_dir, root):
    """ run optimizeContents.pl script from kiwix/tools on /activities """
    args = [
        "perl",
        "optimizeContents.pl",
        "--contentPath={}".format(os.path.join(root, "activities")),
        "--tmpDir=/tmp",
    ]
    optim = subprocess.run(
        args, cwd=os.path.join(working_dir, "dumping_tools", "scripts")
    )
    optim.check_returncode()


def fname_for_title(title):
    """ turn a title into a ZIM-friendly HTML file name """
    return "{}.html".format(
        title.strip()
        .replace("/", "_")
        .replace("?", "")
        .replace("&", " et ")
        .replace("#", "")
        .replace('"', "")
        .replace("'", "")
    )


def indent_json_files(json_root):
    """ re-save all JSON files with indentation (easier debugging) """
    for fname in os.listdir(json_root):
        fpath = os.path.join(json_root, fname)
        with open(fpath, "r") as fp:
            obj = json.load(fp)
        with open(fpath, "w") as fp:
            json.dump(obj, fp, indent=4)


def fix_json_files(json_root):
    """ updates links onto all activities JSON files

        links includes blobs (PDF, image, etc) and media (mp3, image, video) """

    for fname in os.listdir(json_root):
        fpath = os.path.join(json_root, fname)

        content = get_content_of(fpath)

        # inline html (document)
        content = content.replace('src=\\"../activities/', 'src=\\"../../I/activities/')

        content = content.replace('src=\\"/activities/', 'src=\\"../../I/activities/')

        content = content.replace("src='../activities/", "src='../../I/activities/")

        content = content.replace("src='/activities/", "src='../../I/activities/")

        # reload json to make sure we didn't break format
        json.loads(content)

        save_content_to(content, fpath)


def add_fonts(root):
    """ copy missing web fonts to web/fonts/ """
    fpath = os.path.join(root, "web", "fonts")
    if not os.path.exists(fpath):
        logger.info(f"Creating {fpath}")
        os.makedirs(fpath, exist_ok=True)

    for ext in ("eot", "ttf", "woff"):
        font_fname = f"glyphicons-halflings-regular.{ext}"
        font_fpath = os.path.join(fpath, font_fname)
        if not os.path.exists(font_fpath):
            src_fpath = os.path.join(os.path.dirname(__file__), "fonts", font_fname)
            logger.info(f"Copying {src_fpath} -> {font_fpath}")
            shutil.copy(src_fpath, font_fpath)


def fix_scorm_html(root):
    """ fix dynamic JS/CSS/JSON links """

    fpath = os.path.join(root, "activity", "scorm.html")
    content = get_content_of(fpath)

    # use favicon
    if "shortcut icon" not in content:
        content = content.replace(
            "</head>",
            '  <link rel="shortcut icon" '
            'href="../../I/favicon.png" '
            'type="image/png">\n</head>',
        )

    # cancel kiwix-serve bar (not visible) padding
    content = content.replace(
        '<body id="lxxlroot">', '<body id="lxxlroot" style="padding-top: 0 !important">'
    )

    content = content.replace(
        "jsBoot.loader.use('/../web", "jsBoot.loader.use('../../-/web"
    )

    content = content.replace(
        "jsBoot.loader.use('../web", "jsBoot.loader.use('../../-/web"
    )

    content = content.replace(
        'actjson = "../activities/json', 'actjson = "../../-/activities/json'
    )

    content = content.replace(
        "setupTemplate('activity.tpl')",
        "setupTemplate('../../A/activity/activity.tpl')",
    )

    save_content_to(content, fpath)


def fix_index_html(root):
    """ update links in homepage to prevent target=_blank and use human URL """

    fpath = os.path.join(root, "index.html")
    content = get_content_of(fpath)

    # use favicon
    if "shortcut icon" not in content:
        content = content.replace(
            "</head>",
            '   <link rel="shortcut icon" '
            'href="../I/favicon.png" '
            'type="image/png">\n</head>',
        )

    # remove target=_blank on links
    content = content.replace(" target='_blank'", "")

    # replace old scorm.html link by titled-one
    content = content.replace(
        "<a href='activity/scorm.html?id=\" + act[k]['en_id'] + \"'>",
        "<a href='activités/\" + act[k]['fname'] + \"'>",
    )

    save_content_to(content, fpath)


def add_favicon(root):
    """ add external favicon (was none) """

    fpath = os.path.join(root, "favicon.png")
    if not os.path.exists(fpath):
        # assume there's an icon next to this script
        icon_fpath = os.path.join(os.path.dirname(__file__), "favicon.png")
        shutil.copy(icon_fpath, fpath)

    # duplicate icon as workaround to zimwriterfs
    shutil.copy(fpath, os.path.join(root, "I-favicon.png"))


def remove_extra_files(root):
    """ remove maintenance files, not being used """

    for fname in (
        "activities/activities.js",
        "activities/activities.xls",
        "activities/activities.xlsx",
        "activities/index.html",
        "activity/scorm.html",
    ):
        fpath = os.path.join(root, "activities", fname)
        if os.path.exists(fpath):
            os.unlink(fpath)


def gen_activities_html(root):
    """ generate one HTML file for each activity so it's available in /A/ and search """

    # create destination folder
    dest_folder = os.path.join(root, "activités")
    if not os.path.exists(dest_folder):
        logger.info(f"Creating {dest_folder}")
        os.makedirs(dest_folder, exist_ok=True)

    # build list of activities (ID/title)
    activities = {}
    json_root = os.path.join(root, "activities", "json")
    for fname in os.listdir(json_root):
        fpath = os.path.join(json_root, fname)
        with open(fpath, "r") as fp:
            jsd = json.load(fp)
        act_id = fname[3:-5]
        title = jsd["published"]["title"]
        if title in activities.values():
            title += "-B"
        activities[act_id] = title

    # prepare template
    template = get_content_of(os.path.join(root, "activity", "scorm.html"))
    template = template.replace(
        '<title dir="ltr">Activité Éducation et Numérique</title>',
        '<title dir="ltr">__TITLE__</title>',
    )
    template = template.replace(
        'var actjson = "" + location.search.substr(1).split(/\?/);',
        'var actjson = "id=__ACT_ID__";',
    )

    for act_id, act_title in activities.items():
        fname = fname_for_title(act_title)
        save_content_to(
            template.replace("__TITLE__", act_title).replace("__ACT_ID__", act_id),
            os.path.join(dest_folder, fname),
        )

    # dependencies.min.js
    fpath = os.path.join(root, "web", "js", "dependencies.min.js")
    content = get_content_of(fpath)
    act_start = content.index("var act=") + 8
    act_end = content.index(';if("undefined"==typeof jQuery)throw new Error("Bootstrap')
    act_string = content[act_start:act_end]

    cycle, matter, description, title, level, author, en_id = (
        "cycle",
        "matter",
        "description",
        "title",
        "level",
        "author",
        "en_id",
    )
    act_data = eval(act_string)

    for index, info in enumerate(act_data):
        fname = fname_for_title(activities[info["en_id"]])  # own title from ID
        act_data[index].update({"fname": fname})

    new_act = repr(act_data)

    new_js = content[0:act_start] + new_act + content[act_end:]

    save_content_to(new_js, fpath)

    # remove seen() function trying to POST data on visits
    fpath = os.path.join(root, "web", "js", "lxxl-standalone-library-min.js")
    content = get_content_of(fpath)

    content = content.replace(
        "t.query(t.POST,{service:i,onsuccess:e,onfailure:h(n),id:_,command:s})", ""
    )

    save_content_to(content, fpath)

    # activity.tpl
    fpath = os.path.join(root, "activity", "activity.tpl")
    content = get_content_of(fpath)

    content = content.replace(' target="_blank"', "")

    if "home" not in content:
        content = content.replace(
            "<header>",
            '<nav id="home" style="padding: .5em;">'
            '<a href="../../index.html">'
            '<img src="../web/img/LogoE&N.png" '
            'title="Retour à l\'accueil" '
            'style="height: 2em;" /></a>'
            "</nav>\n\n  <header>",
        )

    save_content_to(content, fpath)

    # dependencies.min.css
    # allow kiwix-serve bar to be displayed
    fpath = os.path.join(root, "web", "css", "dependencies.min.css")
    content = get_content_of(fpath)

    # remove position fixed so we can be after taskbar on kiwix-serve
    content = content.replace(
        ".navbar-fixed-bottom,.navbar-fixed-top{position:fixed;",
        ".navbar-fixed-bottom,.navbar-fixed-top{",
    )

    # remove padding so we can be on top on desktop
    content = content.replace("body{padding-top:50px;", "body{")

    # header should not be on top of kiwix-serve bar
    content = content.replace("z-index:1030", "z-index:100")

    save_content_to(content, fpath)


def remove_extra_blobs(root):
    """ remove blobs/* files which are not included in activities content """

    # load all json files into a single large string (!)
    large_index = ""
    json_dir = os.path.join(root, "activities", "json")
    for fname in os.listdir(json_dir):
        with open(os.path.join(json_dir, fname), "r") as fp:
            large_index += fp.read()

    # loop over all blob file names and find out which ones are not called.
    for fname in os.listdir(os.path.join(root, "activities", "blobs")):
        rel_path = f"activities/blobs/{fname}"
        if rel_path not in large_index:
            logger.debug(f"File {rel_path} not used. removing")
            os.unlink(os.path.join(root, rel_path))


def get_checksum(fpath, func=hashlib.md5):
    h = func()
    with open(fpath, "rb") as f:
        for chunk in iter(lambda: f.read(2 ** 20 * 8), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(output_dir, url, fname, checksum):
    """ downloads URL to fname if it doesn't exists or mismatch checksum """
    fpath = os.path.join(output_dir, fname)
    if os.path.exists(fpath):
        logger.info(f"calculating sum for {fpath}...")
        if get_checksum(fpath) == checksum:
            logger.info("  sum MATCHES.")
            return fpath
        logger.info("  sum MISMATCHES.")
        os.unlink(fpath)

    aria2c = subprocess.run(["aria2c", f"--dir={output_dir}", f"--out={fname}", url])
    aria2c.check_returncode()
    return fpath


def extract_archive(archive_fpath, working_dir):
    """ extracts ZIP file into working_dir """

    with zipfile.ZipFile(archive_fpath, "r") as zip_archive:
        zip_archive.extractall(working_dir)
    # remove extra folder from zip file
    shutil.rmtree(os.path.join(working_dir, "__MACOSX"))


def create_zim(root, outputdir, zimfname):
    """ runs zimwriterfs """
    args = [
        "zimwriterfs",
        "--welcome=index.html",
        "--favicon=I-favicon.png",
        "--language=fra",
        '--title="Éducation et Numérique"',
        '--description="Catalogue de ressources pédagogiques intéractives"',
        '--creator="Éducation & Numérique"',
        '--publisher="Kiwix"',
        "--verbose",
        '--name="education-et-numerique_fr"',
        root,
        os.path.join(outputdir, zimfname),
    ]

    logger.debug("Calling: " + " ".join(args))
    zimwriterfs = subprocess.run(args)
    zimwriterfs.check_returncode()


def run(zipurl, zipfname, zipsum, workdir, outputdir, zimfname, debug):
    logger.info("Starting E&N scrapper")
    working_dir = os.path.abspath(os.path.expanduser(workdir))
    root = os.path.join(working_dir, "e-et-n")
    if os.path.exists(root):
        raise IOError(f"Destination folder {root} already exists. exiting.")

    logger.info("Retrieving kiwix tools scripts")
    download_kiwix_tools(working_dir)

    logger.info(f"Retrieving {zipurl}")
    archive_fpath = download_file(working_dir, zipurl, zipfname, zipsum)

    logger.info(f"Extracting {zipfname} into {root}")
    extract_archive(archive_fpath, working_dir)

    # /favicon.png
    logger.info("Adding missing favicon(s)")
    add_favicon(root)

    # /web/fonts
    logger.info("Adding missing fonts")
    add_fonts(root)

    # /activity/scorm.html
    logger.info("Fixing activity file and template")
    fix_scorm_html(root)

    # /index.html
    logger.info("Fixing links in homepage")
    fix_index_html(root)

    # /activities/json
    logger.info("Un-minifying JSON files")
    indent_json_files(os.path.join(root, "activities", "json"))

    logger.info("Fixing links in JSON files")
    fix_json_files(os.path.join(root, "activities", "json"))

    # /activity/xxx.html
    logger.info("Generating individual pages for each activity")
    gen_activities_html(root)

    # /activities and /activity
    logger.info("Removing extra files")
    remove_extra_files(root)

    logger.info("Finding and removing unused blobs")
    remove_extra_blobs(root)

    # /activities
    logger.info("Optimizing media files")
    optimize_content(working_dir, root)

    logger.info("Done preparing folder, executing zimwriterfs")
    create_zim(root, outputdir, zimfname)

    logger.info("All done. 👏")


def main():
    parser = argparse.ArgumentParser(description="Éducation & Numérique scrapper")
    parser.add_argument(
        "--zipurl",
        help="URL to E&N zip file",
        default="http://download.kiwix.org/other/e-et-n.zip",
    )
    parser.add_argument(
        "--zipfname", help="filename to save URL to", default="e-et-n.zip"
    )
    parser.add_argument(
        "--zipsum",
        help="checksum of E&N zip file",
        default="f8db4e6dabb7031ae4e9e6960aa5a749",
    )
    parser.add_argument("--workdir", help="Directory to work from", default=os.getcwd())
    parser.add_argument(
        "--outputdir", help="Directory to save ZIM file to", default="/output"
    )
    parser.add_argument(
        "--zimfname",
        help="Filename to save ZIM file into",
        default="education-et-numerique_fr_2014-12.zim",
    )
    parser.add_argument(
        "--debug", help="Enable verbose output", action="store_true", default=False
    )

    args = parser.parse_args()
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    try:
        run(**dict(args._get_kwargs()))
    except Exception as exc:
        logger.error(f"FAILED. An error occured: {exc}")
        if args.debug:
            logger.exception(exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
