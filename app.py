import os
import shutil
import tempfile

import streamlit as st
import pandas as pd

# import your functions from your main logic file
import course_df as core
# if your file name is different, change `course_df` accordingly


# ------------------------ helper: run full pipeline ------------------------ #
# def run_full_pipeline(excel_path: str, buffer: int, mode: str,
#                       output_dir: str = "output",
#                       photos_dir: str = "photos"):
#     """
#     One-call wrapper that:
#       1. builds result dict from excel_path
#       2. checks clashes
#       3. allocates rooms for ALL dates & shifts
#       4. generates all room-wise Excels + PDFs
#       5. generates overall seating + seats_left Excels
#     """
#
#     # 1. build result
#     result = core.build_course_dicts(excel_path)
#
#     # 2. clash detection (returns list; your function already prints summary)
#     clash_list = core.detect_clashes(result)
#
#     # 3. load rooms sheet
#     rooms_df = pd.read_excel(excel_path, sheet_name="in_room_capacity")
#
#     # 4. PDF logger
#     logger = core.get_pdf_logger(output_dir)
#
#     # 5. allocation + per-room Excels + PDFs
#     for date_str in result.keys():
#         for shift in ["Morning", "Evening"]:
#             room_alloc = core.allocate_shift_for_date(
#                 result, date_str, shift, rooms_df, buffer, mode
#             )
#             if not room_alloc:
#                 continue
#
#             core.export_shift_excels(
#                 result,
#                 date_str,
#                 shift,
#                 room_alloc,
#                 base_output_dir=output_dir,
#                 photos_dir=photos_dir,
#                 logger=logger,
#             )
#
#     # 6. summary Excels
#     core.generate_overall_seating_excel(
#         result, rooms_df, buffer, mode, output_dir=output_dir
#     )
#     core.generate_seats_left_excel(
#         result, rooms_df, buffer, mode, output_dir=output_dir
#     )
#
#     return clash_list


def run_full_pipeline(excel_path: str, buffer: int, mode: str,
                      output_dir: str = "output",
                      photos_dir: str = "photos"):
    """
    One-call wrapper that:
      1. builds result dict from excel_path
      2. checks clashes
      3. allocates rooms for ALL dates & shifts
      4. generates all room-wise Excels + PDFs
      5. generates overall seating + seats_left Excels

    Returns:
        clash_list, failed_slots
    """

    # 1. build result
    result = core.build_course_dicts(excel_path)

    # 2. clash detection
    clash_list = core.detect_clashes(result)

    # 3. load rooms sheet
    rooms_df = pd.read_excel(excel_path, sheet_name="in_room_capacity")

    # 4. PDF logger – IMPORTANT: log OUTSIDE temp dir
    logger = core.get_pdf_logger("output")   # <--- not in tmp_output_dir

    failed_slots = []

    # 5. allocation + per-room Excels + PDFs
    for date_str in result.keys():
        for shift in ["Morning", "Evening"]:
            try:
                room_alloc = core.allocate_shift_for_date(
                    result, date_str, shift, rooms_df, buffer, mode
                )
            except ValueError as e:
                msg = f"{date_str} {shift}: {e}"
                logger.error(msg)
                failed_slots.append(msg)
                # skip this slot, continue others
                continue

            if not room_alloc:
                continue

            core.export_shift_excels(
                result,
                date_str,
                shift,
                room_alloc,
                base_output_dir=output_dir,
                photos_dir=photos_dir,
                logger=logger,
            )

    # 6. summary Excels
    core.generate_overall_seating_excel(
        result, rooms_df, buffer, mode, output_dir=output_dir
    )
    core.generate_seats_left_excel(
        result, rooms_df, buffer, mode, output_dir=output_dir
    )

    return clash_list, failed_slots



# ------------------------------ Streamlit UI ------------------------------ #

st.set_page_config(page_title="MTP Exam Seating & Attendance Generator",
                   page_icon="🪑",
                   layout="centered")

st.title("🪑 Exam Seating & Attendance Generator")

st.markdown(
    "Upload the **input Excel** (same structure as `input_data_tt.xlsx`), "
    "choose buffer & mode:"
)

uploaded_file = st.file_uploader(
    "Upload input Excel file", type=["xlsx"], accept_multiple_files=False
)

col1, col2 = st.columns(2)
with col1:
    buffer = st.number_input(
        "Buffer per room", min_value=0, max_value=50, value=5, step=1
    )
with col2:
    mode = st.selectbox("Mode", ["Sparse", "Dense"])

run_button = st.button("🚀 Run Allocation & Generate Outputs")

# if run_button:
#     if uploaded_file is None:
#         st.error("Please upload an input Excel file first.")
#     else:
#         # use a temp directory so we don't pollute working dir
#         with tempfile.TemporaryDirectory() as tmpdir:
#             # save uploaded excel to temp path
#             tmp_excel_path = os.path.join(tmpdir, "input.xlsx")
#             with open(tmp_excel_path, "wb") as f:
#                 f.write(uploaded_file.getbuffer())
#
#             # create an output folder inside tempdir
#             tmp_output_dir = os.path.join(tmpdir, "output")
#             os.makedirs(tmp_output_dir, exist_ok=True)
#
#             st.info("Running allocation. This may take a little while...")
#
#             try:
#                 clash_list = run_full_pipeline(
#                     excel_path=tmp_excel_path,
#                     buffer=buffer,
#                     mode=mode,
#                     output_dir=tmp_output_dir,
#                     photos_dir="photos",  # assumes photos/ is in working dir
#                 )
#
#                 # move the temp output directory to local 'output'
#                 final_output_dir = "output"
#                 # remove old output if it exists
#                 if os.path.exists(final_output_dir):
#                     shutil.rmtree(final_output_dir)
#                 shutil.move(tmp_output_dir, final_output_dir)
#
#                 st.success("Done! All files generated in the `output` folder.")
#
#                 # brief clash summary on UI
#                 if not clash_list:
#                     st.success("No clashes found. ✅")
#                 else:
#                     st.warning(f"Clashes detected: {len(clash_list)}")
#                     with st.expander("Show clash details"):
#                         for c in clash_list:
#                             st.write(
#                                 f"**{c['date']} {c['shift']}** – "
#                                 f"{c['course1']} ↔ {c['course2']} "
#                                 f"({c['count']} common students)"
#                             )
#
#                 # create a zip of the output folder for download
#                 zip_path = shutil.make_archive("output", "zip", final_output_dir)
#                 with open(zip_path, "rb") as f:
#                     st.download_button(
#                         "⬇️ Download output.zip",
#                         f,
#                         file_name="output.zip",
#                         mime="application/zip",
#                     )
#
#                 st.info("You can also find the `output` folder next to this app.")
#
#             except Exception as e:
#                 st.error("Something went wrong during generation. "
#                          "Check `output/pdf_errors.log` for details if it exists.")
#                 st.exception(e)

if run_button:
    if uploaded_file is None:
        st.error("Please upload an input Excel file first.")
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_excel_path = os.path.join(tmpdir, "input.xlsx")
            with open(tmp_excel_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            tmp_output_dir = os.path.join(tmpdir, "output")
            os.makedirs(tmp_output_dir, exist_ok=True)

            st.info("Running allocation. This may take a little while...")

            try:
                clash_list, failed_slots = run_full_pipeline(
                    excel_path=tmp_excel_path,
                    buffer=buffer,
                    mode=mode,
                    output_dir=tmp_output_dir,
                    photos_dir="photos",
                )

                # move temp output -> final output
                # final_output_dir = "output"
                # if os.path.exists(final_output_dir):
                #     shutil.rmtree(final_output_dir)
                # shutil.move(tmp_output_dir, final_output_dir)
                import logging  # put at top of file if not already

                ...

                final_output_dir = "output"
                if os.path.exists(final_output_dir):
                    # close all logging handlers so Windows releases pdf_errors.log
                    logging.shutdown()
                    shutil.rmtree(final_output_dir)

                shutil.move(tmp_output_dir, final_output_dir)

                st.success("Done! All files generated in the `output` folder.")

                # clashes
                if not clash_list:
                    st.success("No clashes found. ✅")
                else:
                    st.warning(f"Clashes detected: {len(clash_list)}")
                    with st.expander("Show clash details"):
                        for c in clash_list:
                            st.write(
                                f"**{c['date']} {c['shift']}** – "
                                f"{c['course1']} ↔ {c['course2']} "
                                f"({c['count']} common students)"
                            )

                # failed slots (not enough capacity)
                if failed_slots:
                    st.error(f"Could not allocate some slots (capacity too low):")
                    with st.expander("Show allocation capacity errors"):
                        for msg in failed_slots:
                            st.write(msg)

                # make zip for download
                zip_path = shutil.make_archive("output", "zip", final_output_dir)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download output.zip",
                        f,
                        file_name="output.zip",
                        mime="application/zip",
                    )

            except Exception as e:
                st.error("Something went wrong during generation.")
                st.exception(e)

