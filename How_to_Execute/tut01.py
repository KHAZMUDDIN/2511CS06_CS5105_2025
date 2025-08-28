import streamlit as st
import pandas as pd
import re, io, zipfile

st.title("Student Grouping")

def extract_branch_code(roll_number):
    match = re.search(r"[A-Za-z]+", str(roll_number))
    return match.group(0).upper() if match else "UNKNOWN"

def interleave_by_branch(rows):
    by_branch = {}
    for r in rows:
        b = r["Branch"]
        by_branch.setdefault(b, []).append(r)
    order = []
    branches = sorted(by_branch.keys())
    while any(by_branch[b] for b in branches):
        for b in branches:
            if by_branch[b]:
                order.append(by_branch[b].pop(0))
    return order

# -------- Grouping strategies --------
# def round_robin_groups(student_data, n_groups):
#     # distribute students to groups by cycling branches alphabetically
#     groups = [[] for _ in range(n_groups)]
#     branch_queues = {b: g.to_dict("records") for b, g in student_data.groupby("Branch")}
#     branches = sorted(branch_queues.keys())
#
#     idx = 0
#     while any(branch_queues.values()):
#         for b in branches:
#             if branch_queues[b]:
#                 groups[idx % n_groups].append(branch_queues[b].pop(0))
#                 idx += 1
#
#     groups = [interleave_by_branch(g) for g in groups]
#     return groups

def round_robin_groups(student_data, n_groups):
    groups = [[] for _ in range(n_groups)]
    branches = sorted(student_data["Branch"].unique())

    for b in branches:
        records = student_data[student_data["Branch"] == b].to_dict("records")
        for i, r in enumerate(records):
            groups[i % n_groups].append(r)

    groups = [interleave_by_branch(g) for g in groups]
    return groups


def uniform_groups(student_data, n_groups):
    total = len(student_data)
    q, r = divmod(total, n_groups)
    target_sizes = [q + 1 if i < r else q for i in range(n_groups)]

    groups = [[] for _ in range(n_groups)]
    # sort branches by descending size
    branch_sizes = student_data["Branch"].value_counts().to_dict()
    branch_queues = {b: g.to_dict("records") for b, g in student_data.groupby("Branch")}
    branches = sorted(branch_queues.keys(), key=lambda b: branch_sizes[b], reverse=True)

    branch_idx = 0
    for gi in range(n_groups):
        need = target_sizes[gi]
        while need > 0 and any(branch_queues.values()):
            b = branches[branch_idx % len(branches)]
            if branch_queues[b]:
                groups[gi].append(branch_queues[b].pop(0))
                need -= 1
            else:
                branch_idx += 1
                continue
    return groups

# -------- ZIP builder --------
def build_zip(student_data, n_groups):
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, "w") as zipf:
        # branches/
        for b, g in student_data.groupby("Branch"):
            zipf.writestr(f"branches/{b}.csv",
                          g.to_csv(index=False).encode("utf-8"))

        # round_robin/
        rr = round_robin_groups(student_data, n_groups)
        for i, g in enumerate(rr, 1):
            zipf.writestr(f"round_robin/group_{i}.csv",
                          pd.DataFrame(g)[["Roll","Name","Email","Branch"]]
                          .to_csv(index=False).encode("utf-8"))

        # uniform/
        uni = uniform_groups(student_data, n_groups)
        for i, g in enumerate(uni, 1):
            zipf.writestr(f"uniform/group_{i}.csv",
                          pd.DataFrame(g)[["Roll","Name","Email","Branch"]]
                          .to_csv(index=False).encode("utf-8"))

        all_branches = sorted(student_data["Branch"].unique())
        summary_csv = make_summary_csv(rr, uni, all_branches)
        zipf.writestr("grouping_summary.csv", summary_csv)

    return mem_zip.getvalue()

def make_summary_csv(rr_groups, uniform_groups, all_branches):
    output = io.StringIO()

    # Round Robin summary
    rr_data = []
    for idx, group in enumerate(rr_groups, 1):
        df = pd.DataFrame(group)
        counts = df["Branch"].value_counts().reindex(all_branches, fill_value=0).to_dict()
        counts["Total"] = len(df)
        counts["Group"] = f"G{idx}"
        rr_data.append(counts)

    rr_df = pd.DataFrame(rr_data).set_index("Group")
    rr_df = rr_df[all_branches + ["Total"]]
    output.write("Round Robin Grouping Summary\n")
    rr_df.to_csv(output)
    output.write("\n\n")

    # Uniform summary
    uniform_data = []
    for idx, group in enumerate(uniform_groups, 1):
        df = pd.DataFrame(group)
        counts = df["Branch"].value_counts().reindex(all_branches, fill_value=0).to_dict()
        counts["Total"] = len(df)
        counts["Group"] = f"G{idx}"
        uniform_data.append(counts)

    uniform_df = pd.DataFrame(uniform_data).set_index("Group")
    uniform_df = uniform_df[all_branches + ["Total"]]
    output.write("Uniform Grouping Summary\n")
    uniform_df.to_csv(output)

    return output.getvalue().encode("utf-8")


# -------- UI --------
file = st.file_uploader("Upload CSV", type=["csv"])
n_groups = st.number_input("Number of groups (N)", min_value=2, value=5, step=1)

if file and n_groups:
    try:
        df = pd.read_csv(file)[["Roll", "Name", "Email"]]
    except Exception:
        st.error("CSV must contain columns: Roll, Name, Email")
    else:
        df["Branch"] = df["Roll"].apply(extract_branch_code)

        if st.button("Generate ZIP"):
            zip_bytes = build_zip(df, int(n_groups))
            st.download_button("Download ZIP",
                               data=zip_bytes,
                               file_name="student_groups.zip",
                               mime="application/zip")

