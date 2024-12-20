#!/usr/bin/env python

import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF


def create_performance_table(data: pd.DataFrame, file_size: int):
    """Creates a performance table for a specific file size."""

    df_filtered = data[(data["filepath"] == f"test_data_{file_size}.txt")]
    df_sorted = df_filtered.sort_values(by="avg_time")
    return df_sorted[["algorithm", "avg_time", "reread_on_query"]]


def create_file_size_table(data: pd.DataFrame, algorithm_name: str):
    """Creates a table showing the effect of file size on a specific algorithm."""
    df_filtered = data[data["algorithm"] == algorithm_name]
    df_sorted = df_filtered.sort_values(by="filepath")
    return df_sorted[["filepath", "avg_time", "reread_on_query"]]


def create_concurrency_table(
    data: pd.DataFrame, algorithm_name: str, file_path: str
):
    """Creates a table to show the effects of concurrency"""
    df_filtered = data[
        (data["algorithm"] == algorithm_name) & (data["filepath"] == file_path)
    ]
    df_sorted = df_filtered.sort_values(by="num_concurrent")
    return df_sorted[["num_concurrent", "avg_time", "total_time"]]


def create_performance_graph(data: pd.DataFrame, output_path: str):
    """Generates a performance graph using the data."""
    plt.figure(figsize=(12, 6))

    # Filter for reread_on_query=False
    df_false = data[data["reread_on_query"] == False]
    for algorithm in df_false["algorithm"].unique():
        df_algo = df_false[df_false["algorithm"] == algorithm]
        file_sizes = [
            int(path.split("_")[-1].split(".")[0])
            for path in df_algo["filepath"]
        ]
        plt.plot(
            file_sizes, df_algo["avg_time"], label=f"{algorithm} (reread=False)"
        )

    # Filter for reread_on_query=True
    df_true = data[data["reread_on_query"] == True]
    for algorithm in df_true["algorithm"].unique():
        df_algo = df_true[df_true["algorithm"] == algorithm]
        file_sizes = [
            int(path.split("_")[-1].split(".")[0])
            for path in df_algo["filepath"]
        ]
        plt.plot(
            file_sizes,
            df_algo["avg_time"],
            label=f"{algorithm} (reread=True)",
            linestyle="--",
        )

    plt.xlabel("File Size (Number of Lines)")
    plt.ylabel("Average Time (seconds)")
    plt.title("Algorithm Performance vs. File Size")
    plt.legend()
    plt.grid(True)
    plt.savefig(output_path, format="pdf")


def create_pdf_report(
    data_reread_false: str,
    data_reread_true: str,
    concurrency_data: str,
    report_path: str,
):
    """Creates the PDF report."""

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Speed Test Report", ln=True, align="C")

    # Methodology
    pdf.cell(200, 10, txt="Methodology", ln=True, align="L")
    pdf.cell(
        200,
        10,
        txt="This report details performance analysis of various file search algorithms.",
        ln=True,
        align="L",
    )

    # File size analysis
    pdf.cell(200, 10, txt="File size analysis", ln=True, align="L")
    df_reread_false = pd.read_csv(data_reread_false)
    fastest_algorithm = df_reread_false.sort_values(by="avg_time").iloc[0][
        "algorithm"
    ]
    for size in [10000, 100000, 250000, 500000, 750000, 1000000]:
        table_data = create_performance_table(df_reread_false, size)
        pdf.cell(
            200,
            10,
            txt=f"Performance of different algorithms for file size of: {size}",
            ln=True,
            align="L",
        )
        pdf.cell(10, 10, txt=str(table_data.to_string()), ln=True, align="L")

    pdf.cell(
        200,
        10,
        txt="File size performance for the fastest Algorithm",
        ln=True,
        align="L",
    )
    table_data = create_file_size_table(df_reread_false, fastest_algorithm)
    pdf.cell(10, 10, txt=str(table_data.to_string()), ln=True, align="L")

    # Concurrency analysis
    pdf.cell(200, 10, txt="Concurrency analysis", ln=True, align="L")
    df_concurrency = pd.read_csv(concurrency_data)
    for file_path in df_concurrency["filepath"].unique():
        table_data = create_concurrency_table(
            df_concurrency, fastest_algorithm, file_path
        )
        pdf.cell(
            200,
            10,
            txt=f"Concurrency test results for {file_path}",
            ln=True,
            align="L",
        )
        pdf.cell(10, 10, txt=str(table_data.to_string()), ln=True, align="L")

    # Graphs
    pdf.cell(200, 10, txt="Performance Graph", ln=True, align="L")
    create_performance_graph(
        pd.read_csv(data_reread_false).append(pd.read_csv(data_reread_true)),
        "performance_graph.pdf",
    )
    pdf.image("performance_graph.pdf", w=180)

    pdf.output(report_path)


if __name__ == "__main__":
    # Example usage
    file_sizes = [10000, 100000, 250000, 500000, 750000, 1000000]
    queries = [
        "test string 5000",
        "non existing string",
        "test string 1000",
        "test string 1000000",
    ]
    num_runs = 10
    num_concurrent = [1, 10, 50, 100, 200]

    filepaths = []
    for file_size in file_sizes:
        filepath = f"test_data_{file_size}.txt"
        generate_test_file(filepath, file_size)
        filepaths.append(filepath)

    data_reread_true = collect_speed_test_data(
        filepaths, queries, num_runs, reread_on_query=True
    )
    save_test_data(data_reread_true, "speed_test_data_reread_true.csv")

    data_reread_false = collect_speed_test_data(
        filepaths, queries, num_runs, reread_on_query=False
    )
    save_test_data(data_reread_false, "speed_test_data_reread_false.csv")

    concurrency_data = collect_speed_test_data(
        filepaths, queries, num_runs, reread_on_query=False, num_concurrent=10
    )
    save_test_data(concurrency_data, "concurrency_test_data.csv")

    create_pdf_report(
        "speed_test_data_reread_false.csv",
        "speed_test_data_reread_true.csv",
        "concurrency_test_data.csv",
        "speed_report.pdf",
    )
