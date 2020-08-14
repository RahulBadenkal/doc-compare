"""
Methods for computing differences between documents
"""

import subprocess
import os
from lxml import etree
import logging

import eel
import fitz

from core.utils.sysutils import get_filename_and_type, subprocess_args
from core.utils.strutils.strutils import get_text_diffs
from core.utils.dbgutils import time_tracker

from settings import BINPATHS, OUTPUTDIR, TEMPDIR
from app import doctopdf
from app.js_func import progress_msg


def get_output_filepaths(filepath1, filepath2):
    file_name, file_extension = get_filename_and_type(filepath1)
    original_doc = os.path.abspath(os.path.join(OUTPUTDIR, file_name + " (Master)" + file_extension))
    file_name, file_extension = get_filename_and_type(filepath2)
    revised_doc = os.path.abspath(os.path.join(OUTPUTDIR, file_name + " (Revised)" + file_extension))
    return original_doc, revised_doc


############################################################
#           Convert the given file to pdf                  #
############################################################
@time_tracker
def convert_docs_to_pdf(infilelist):
    new_filepaths = []
    for i, filepath in enumerate(infilelist):
        filename, file_extension = get_filename_and_type(filepath)
        if file_extension == ".pdf":
            new_filepaths.append({'old': filepath, 'new': filepath, 'convert': False})
        elif file_extension not in doctopdf.supported_filetypes:
            raise ValueError("File type '{}' is not supported".format(file_extension))
        else:
            # TODO: After Fixing the libreoffice conversion bug, rename the files to "{} ({})".format(filename, i)
            #  This will help avoid problems when converting two different files with the same file name. For ex:
            #  The program will fail when file1 = 'C:/Documents/abcd.docx' and file2 = 'C:/Desktop/abcd.docx'
            new_filename = "{}".format(filename)
            new_filepath = os.path.abspath(os.path.join(TEMPDIR, new_filename + ".pdf"))
            new_filepaths.append({'old': filepath, 'new': new_filepath, 'convert': True})

    a = [each['old'] for each in new_filepaths if each['convert'] is True]
    b = [each['new'] for each in new_filepaths if each['convert'] is True]

    for each in b:
        # Delete the outfile if it exists
        if os.path.isfile(each):
            os.remove(each)
    if len(a) != 0:  # There are some non pdf files
        # TODO: Fix the saveAs Window that pops up when saving word to pdf using MS Word
        doc_to_pdf_retval = doctopdf.doc_to_pdf(a, b)
        if doc_to_pdf_retval['result'] is False:
            raise ValueError(doc_to_pdf_retval['errmsg'])
        logging.info(doc_to_pdf_retval['errmsg'])  # Success

    return [each['new'] for each in new_filepaths]


############################################################
#             PDF to text With location                    #
############################################################
@time_tracker
def serialize_pdf(i, fn, top_margin, bottom_margin):
    box_generator = pdf_to_bboxes(i, fn, top_margin, bottom_margin)
    box_generator = mark_eol_hyphens(box_generator)
    return form_continuous_text(box_generator)


def pdf_to_bboxes(pdf_index, fn, top_margin=0, bottom_margin=100):
    # Get the bounding boxes of text runs in the PDF.
    # Each text run is returned as a dict.

    # TODO: Safely kill the subprocess call in case of abrupt closing
    # TODO: Add Support for password protected pdfs
    xml = subprocess.check_output([BINPATHS['pdftotext'], "-bbox", "-raw", fn, "-"], **subprocess_args(False))

    # This avoids PCDATA errors
    codes_to_avoid = [0, 1, 2, 3, 4, 5, 6, 7, 8,
                      11, 12,
                      14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, ]
    cleaned_xml = bytes([x for x in xml if x not in codes_to_avoid])
    dom = etree.fromstring(cleaned_xml)
    page_list = dom.findall(".//{http://www.w3.org/1999/xhtml}page")

    tot_pdf_height = sum([float(page.get("height")) for page in page_list])
    tot_pdf_pages = len(page_list)
    pdfdict = {
        "index": pdf_index,
        "file": fn,
        "tot_pages": tot_pdf_pages,
        "tot_pdf_height": tot_pdf_height,
    }

    box_index = 0
    abs_page_height = 0
    last_page_height = 0
    for i, page in enumerate(page_list):
        abs_page_height += last_page_height
        last_page_height = float(page.get("height"))

        pagedict = {
            "number": i,
            "width": float(page.get("width")),
            "height": float(page.get("height")),
        }
        for word in page.findall("{http://www.w3.org/1999/xhtml}word"):
            if float(word.get("yMax")) < (top_margin / 100.0) * float(page.get("height")):
                continue
            if float(word.get("yMin")) > (bottom_margin / 100.0) * float(page.get("height")):
                continue

            yield {
                "index": box_index,
                "pdf": pdfdict,
                "page": pagedict,
                "xMin": float(word.get("xMin")),
                "yMin": float(word.get("yMin")),
                "abs_y": float(word.get("yMin")) + abs_page_height,
                "xMax": float(word.get("xMax")),
                "yMax": float(word.get("yMax")),
                "text": word.text,
                "type": "word"
            }
            box_index += 1


# TODO: Handle EOL hypenhs (Ex: "reborn" should be considered same as "re-\nborn")
def mark_eol_hyphens(boxes):
    # Replace end-of-line hyphens with discretionary hyphens so we can weed
    # those out later. Finding the end of a line is hard.
    box = None
    for next_box in boxes:
        if box is not None:
            if box['pdf'] != next_box['pdf'] or box['page'] != next_box['page'] \
                    or next_box['yMin'] >= box['yMin'] + (box['yMax'] - box['yMin']) / 2:
                # box was at the end of a line
                mark_eol_hyphen(box)
            yield box
        box = next_box
    if box is not None:
        # The last box is at the end of a line too.
        mark_eol_hyphen(box)
        yield box


def mark_eol_hyphen(box):
    if box['text'] is not None:
        if box['text'].endswith("-"):
            box['text'] = box['text'][0:-1] + "\u00AD"


def form_continuous_text(box_generator):
    boxes = []
    text = []
    textlength = 0
    for run in box_generator:
        if run["text"] is None:
            continue
        normalized_text = run["text"].strip()

        # Ensure that each run ends with a space, since pdftotext
        # strips spaces between words. If we do a word-by-word diff,
        # that would be important.

        # But don't put in a space if the box ends in a discretionary
        # hyphen. Instead, remove the hyphen.
        if normalized_text.endswith("\u00AD"):
            normalized_text = normalized_text[0:-1]

        run["text"] = normalized_text
        run["startIndex"] = textlength
        run["textLength"] = len(normalized_text)
        boxes.append(run)
        text.append(normalized_text)

        endIndex = run["startIndex"] + (run["textLength"] - 1)
        spaceIndex = endIndex + 1  # +1 for a blank space
        nextStartIndex = spaceIndex + 1
        textlength = nextStartIndex

    text = " ".join(text)  # Separate text by one blank space

    return boxes, text


############################################################
#                 Text Diff                                #
############################################################
@time_tracker
def diff(text1, text2):
    # Compute word wise differences between text
    diff_mode = 1
    # First try diffing using JS as it is faster
    diffs = diff_js(text1, text2, diff_mode=diff_mode, timeout=10)
    if diffs is not None:
        # Diff via JS is successful
        pass
    else:
        # If Diff via JS failed then try do diff via python
        diffs = get_text_diffs(text1, text2, diff_mode=diff_mode, timeout=10)
    return diffs


@time_tracker
def diff_js(text1, text2, diff_mode, timeout):
    js_diffs = eel.diff_text(text1, text2, diff_mode, timeout)()
    if js_diffs is not None:
        js_diffs = [(each['0'], each['1']) for each in js_diffs]
    return js_diffs


############################################################
#               Get Diff positions in PDF                  #
############################################################
@time_tracker
def process_hunks(hunks, boxes):
    # Process each diff hunk one by one and look at their corresponding
    # text boxes in the original PDFs.
    offsets = [0, 0]
    changes = []
    for op, opstr in hunks:
        oplen = len(opstr)
        if op == 0:
            # This hunk represents a region in the two text documents that are
            # in common. So nothing to process but advance the counters.
            offsets[0] += oplen
            offsets[1] += oplen
            # Put a marker in the changes so we can line up equivalent parts
            # later.
            if len(changes) > 0 and changes[-1] != '*':
                changes.append("*")
        elif op in (-1, 1):
            # This hunk represents a region of text only in the left (op == "-")
            # or right (op == "+") document. The change is oplen chars long.
            idx = 0 if (op == -1) else 1
            mark_difference(oplen, offsets[idx], boxes[idx], changes)
            offsets[idx] += oplen
        else:
            raise ValueError(op)

    # Remove any final asterisk.
    if len(changes) > 0 and changes[-1] == "*":
        changes.pop()

    return changes


def mark_difference(hunk_length, offset, boxes, changes):
    # We're passed an offset and length into a document given to us
    # by the text comparison, and we'll mark the text boxes passed
    # in boxes as having changed content.

    # Discard boxes whose text is entirely before this hunk
    while len(boxes) > 0 and (boxes[0]["startIndex"] + boxes[0]["textLength"]) <= offset:
        boxes.pop(0)

    # Process the boxes that intersect this hunk. We can't subdivide boxes,
    # so even though not all of the text in the box might be changed we'll
    # mark the whole box as changed.
    while len(boxes) > 0 and boxes[0]["startIndex"] < offset + hunk_length:
        # Mark this box as changed. Discard the box. Now that we know it's changed,
        # there's no reason to hold onto it. It can't be marked as changed twice.
        changes.append(boxes.pop(0))


############################################################
#               Highlight diffs in Pdfs                    #
############################################################
@time_tracker
def highlight_pdf(infiles, outfiles, changes):
    deletion_color_rgb = (0.9333333333333333, 0.8352941176470589, 0.8235294117647058)  # mistyrose2
    insertion_color_rgb = (0.7412, 0.898, 0.7961)  # Misty Green

    # TODO: Make Highlighting of pdfs faster
    for docno in [0, 1]:
        doc_changes = [change for change in changes if change != "*" and change['pdf']['index'] == docno]
        doc_merge_locs = get_merged_changes_loc(doc_changes)
        pdf = fitz.open(infiles[docno])
        if docno == 0:
            color = deletion_color_rgb
        else:
            color = insertion_color_rgb
        for x in doc_merge_locs:
            pageno = x[0]
            xmin, ymin, xmax, ymax = x[1], x[2], x[3], x[4]

            page = pdf[pageno]
            rect = fitz.Rect(xmin, ymin, xmax, ymax)
            highlight = page.addHighlightAnnot(rect)
            highlight.parent = page
            highlight.setColors({'stroke': color})
            highlight.update()

        if os.path.isfile(outfiles[docno]):
            os.remove(outfiles[docno])
        pdf.save(outfiles[docno], garbage=4, deflate=True, clean=True)
        pdf.close()


# Merges two or more consecutive changes together so that it is faster to highlight later on
@time_tracker
def get_merged_changes_loc(changes):
    if len(changes) == 0:
        return []

    new_changes_loc = []
    start_box = 0
    for i in range(len(changes) - 1):
        same_page = changes[i]['page']['number'] == changes[i + 1]['page']['number']
        same_line = round(changes[i]['yMin'] - changes[i + 1]['yMin'], 3) == 0 and \
                    round(changes[i]['yMax'] - changes[i + 1]['yMax'], 3) == 0
        immediate_neighbour = changes[i]['index'] + 1 == changes[i + 1]['index']
        if same_page and same_line and immediate_neighbour:
            continue
        else:
            new_changes_loc.append((start_box, i))
            start_box = i + 1
    if start_box == len(changes) - 1:
        new_changes_loc.append((start_box, start_box))
    else:
        new_changes_loc.append((start_box, len(changes) - 1))

    new_changes = [(changes[start_loc]['page']['number'],  # Page
                    changes[start_loc]['xMin'], changes[start_loc]['yMin'],
                    changes[end_loc]['xMax'], changes[end_loc]['yMax'])
                   for start_loc, end_loc in new_changes_loc]
    return new_changes


############################################################
# API:                                                     #
# Given paths to 2 pdfs, create 2 new pdfs with text       #
# differences between them highlighted                     #
############################################################
@time_tracker
def diff_pdfs(filepath1, filepath2, js_progress_funcname):
    logging.info("Starting PDF Difference")

    # 0. Checking if the files are same
    logging.info("Checking if the files are same")
    if filepath1 == filepath2:
        raise ValueError("Please upload different files")

    # 1. Convert docs to pdf
    progress_msg(js_progress_funcname, "Converting Docs to Pdf")
    logging.info("Converting Docs to Pdf (If required)")
    converted_filepaths = convert_docs_to_pdf([filepath1, filepath2])
    filepath1, filepath2 = converted_filepaths[0], converted_filepaths[1]

    # 2. Get Pdf from text with location info
    progress_msg(js_progress_funcname, "Serializing Pdfs")
    logging.info("Serializing Pdfs")
    docs = [serialize_pdf(0, filepath1, top_margin=0, bottom_margin=100),
            serialize_pdf(1, filepath2, top_margin=0, bottom_margin=100)]

    # 3. Get text diff
    progress_msg(js_progress_funcname, "Getting Text Differences")
    logging.info("Getting Text Differences")
    diffs = diff(docs[0][1], docs[1][1])

    # 4. Get diff locations in pdf
    progress_msg(js_progress_funcname, "Getting Text Differences Positions in PDFs")
    logging.info("Getting Text Differences Positions in PDFs")
    diff_locs = process_hunks(diffs, [docs[0][0], docs[1][0]])

    # 5. Highlight pdf
    progress_msg(js_progress_funcname, "Highlighting PDFs")
    logging.info("Highlighting PDFs")
    infiles = [filepath1, filepath2]
    outfilespath = get_output_filepaths(filepath1, filepath2)
    highlight_pdf(infiles, outfilespath, diff_locs)

    progress_msg(js_progress_funcname, "Loading UI")
    logging.info("Finished")

    return diff_locs, outfilespath
