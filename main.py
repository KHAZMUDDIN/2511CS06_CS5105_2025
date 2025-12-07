import pandas as pd

def get_sheet_names(path):
    excel_file = pd.ExcelFile(path)
    return excel_file.sheet_names

def load_and_print_excel(path):
    # Load all sheets into a dictionary of DataFrames
    sheets = pd.read_excel(path, sheet_name=None)

    # Print sheet names and their content
    # for sheet_name, df in sheets.items():
    #     print(f"\n========== Sheet: {sheet_name} ==========")
    #
    #     # Print column names
    #     print("Columns:", list(df.columns))
    #
    #     # Print first few rows (head)
    #     print("\nSample rows:")
    #     print(df.head().to_string(index=False))

    # print(sheets)

    names = get_sheet_names("input_data_tt.xlsx")
    print(names)

    # df = sheets["in_timetable"]
    # print(df)




if __name__ == '__main__':
    load_and_print_excel("input_data_tt.xlsx")


