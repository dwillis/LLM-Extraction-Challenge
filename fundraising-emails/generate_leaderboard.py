#!/usr/bin/env python3
import os
import csv
import pandas as pd
from datetime import datetime

def generate_leaderboard_html(summary_csv_path, output_path):
    """
    Generate an HTML leaderboard from the summary CSV file,
    with sections for Updated Prompt and Original Prompt.
    :param summary_csv_path: Path to the summary CSV file
    :param output_path: Path to save the output HTML file
    """
    # Read the summary CSV
    try:
        df = pd.read_csv(summary_csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Separate dataframes for updated and original prompts
    df_updated = df[df['JSON Filename'].str.contains('prompt2', case=False)].copy()
    df_original = df[~df['JSON Filename'].str.contains('prompt2', case=False)].copy()

    # Sort both dataframes
    df_updated = df_updated.sort_values(by=['Total Records', 'Committee Matches'], ascending=[False, False])
    df_original = df_original.sort_values(by=['Total Records', 'Committee Matches'], ascending=[False, False])

    # Function to generate table rows
    def generate_table_rows(dataframe, prompt_type):
        def get_match_class(match_pct):
            if match_pct >= 85:
                return 'match-high'
            elif match_pct >= 70:
                return 'match-medium'
            else:
                return 'match-low'

        return "".join([f"""
        <tr data-type="{prompt_type}">
            <td>{row['JSON Filename']}</td>
            <td class="metric-value">{row['Total Records']}</td>
            <td class="metric-value">{row['Committee Matches']}</td>
            <td><span class="match-percent {get_match_class(row['Committee Matches'] / row['Total Records'] * 100)}">{row['Committee Matches'] / row['Total Records'] * 100:.2f}%</span></td>
            <td class="metric-value">{row['Accuracy']:.2f}</td>
            <td class="metric-value">{row['Precision']:.2f}</td>
            <td class="metric-value">{row['Recall']:.2f}</td>
            <td class="metric-value">{row['F1 Score']:.2f}</td>
        </tr>""" for _, row in dataframe.iterrows()])

    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Political Email Extraction Leaderboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .introduction {{
            background-color: #f8f9fa;
            padding: 30px;
            border-left: 4px solid #667eea;
            margin: 30px;
            border-radius: 8px;
        }}

        .introduction p {{
            margin-bottom: 15px;
            font-size: 1.05em;
        }}

        .introduction a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            border-bottom: 2px solid transparent;
            transition: border-bottom 0.3s;
        }}

        .introduction a:hover {{
            border-bottom: 2px solid #667eea;
        }}

        .controls {{
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: center;
        }}

        .search-box {{
            flex: 1;
            min-width: 250px;
        }}

        .search-box input {{
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s, box-shadow 0.3s;
        }}

        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}

        .filter-buttons {{
            display: flex;
            gap: 10px;
        }}

        .filter-btn {{
            padding: 12px 24px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.95em;
            font-weight: 600;
            transition: all 0.3s;
        }}

        .filter-btn:hover {{
            background: #667eea;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}

        .filter-btn.active {{
            background: #667eea;
            color: white;
        }}

        .stats {{
            padding: 10px 30px;
            background: #e7f3ff;
            color: #004085;
            font-weight: 600;
        }}

        .section {{
            padding: 30px;
        }}

        h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            font-weight: 700;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        .table-wrapper {{
            overflow-x: auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}

        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
            cursor: pointer;
            user-select: none;
            transition: background 0.3s;
        }}

        th:hover {{
            background: linear-gradient(135deg, #5568d3 0%, #653a8a 100%);
        }}

        th::after {{
            content: ' ↕';
            opacity: 0.5;
            font-size: 0.8em;
        }}

        td {{
            padding: 14px 16px;
            border-bottom: 1px solid #e9ecef;
        }}

        tr:hover {{
            background-color: #f8f9fa;
        }}

        tr.hidden {{
            display: none;
        }}

        .metric-value {{
            font-weight: 600;
            font-family: 'Courier New', monospace;
        }}

        .match-percent {{
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}

        .match-high {{ background: #d4edda; color: #155724; }}
        .match-medium {{ background: #fff3cd; color: #856404; }}
        .match-low {{ background: #f8d7da; color: #721c24; }}

        .timestamp {{
            text-align: center;
            color: #6c757d;
            padding: 30px;
            font-size: 0.9em;
            background: #f8f9fa;
            border-top: 2px solid #e9ecef;
        }}

        .no-results {{
            text-align: center;
            padding: 60px;
            color: #6c757d;
            font-size: 1.2em;
        }}

        @media (max-width: 768px) {{
            h1 {{
                font-size: 1.8em;
            }}

            .controls {{
                flex-direction: column;
            }}

            .search-box {{
                width: 100%;
            }}

            table {{
                font-size: 0.9em;
            }}

            th, td {{
                padding: 10px 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏆 Political Email Extraction Leaderboard</h1>
            <p>Comparing LLM Performance on Committee Name Extraction</p>
        </header>

        <div class="introduction">
            <p>What kind of sicko signs up for political fundraising emails from just about every committee? Oh, right, that's me. I've collected thousands of political fundraising emails and challenged various LLMs to extract committee names from their disclaimers (like "Paid for by The Pennsylvania Democratic Party"). This extraction isn't straightforward - disclaimers vary in format and position, with some being simple and others continuing with additional text about contributions and treasurers.</p>

            <p>Using the same 1,000 emails from November 2024 and a zero-shot prompt asking models to extract committee names and senders, I've compared how different LLMs perform at this task. The leaderboard below shows each model's success rate at correctly matching the committee names in the training dataset. For more details on this project, read my <a href="https://thescoop.org/archives/2025/01/27/llm-extraction-challenge-fundraising-emails/index.html">full blog post</a>. You can also explore the <a href="https://github.com/dwillis/LLM-Extraction-Challenge">complete code and extraction results on GitHub</a>.</p>
        </div>

        <div class="controls">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="🔍 Search by model name...">
            </div>
            <div class="filter-buttons">
                <button class="filter-btn active" data-filter="all">All Models</button>
                <button class="filter-btn" data-filter="updated">Updated Prompt</button>
                <button class="filter-btn" data-filter="original">Original Prompt</button>
            </div>
        </div>

        <div class="stats" id="stats">
            Showing <span id="visibleCount">0</span> of <span id="totalCount">0</span> models
        </div>

        <div class="section">
            <h2>Updated Prompt Results</h2>
            <div class="table-wrapper">
                <table id="updatedTable">
                    <thead>
                        <tr>
                            <th data-sort="model">Model</th>
                            <th data-sort="total">Total Records</th>
                            <th data-sort="matches">Matches</th>
                            <th data-sort="matchpct">Match %</th>
                            <th data-sort="accuracy">Accuracy</th>
                            <th data-sort="precision">Precision</th>
                            <th data-sort="recall">Recall</th>
                            <th data-sort="f1">F1 Score</th>
                        </tr>
                    </thead>
                    <tbody>
{generate_table_rows(df_updated, 'updated')}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <h2>Original Prompt Results</h2>
            <div class="table-wrapper">
                <table id="originalTable">
                    <thead>
                        <tr>
                            <th data-sort="model">Model</th>
                            <th data-sort="total">Total Records</th>
                            <th data-sort="matches">Matches</th>
                            <th data-sort="matchpct">Match %</th>
                            <th data-sort="accuracy">Accuracy</th>
                            <th data-sort="precision">Precision</th>
                            <th data-sort="recall">Recall</th>
                            <th data-sort="f1">F1 Score</th>
                        </tr>
                    </thead>
                    <tbody>
{generate_table_rows(df_original, 'original')}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="timestamp">
            Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>

    <script>
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const filterBtns = document.querySelectorAll('.filter-btn');
        let currentFilter = 'all';

        searchInput.addEventListener('input', filterTable);

        filterBtns.forEach(btn => {{
            btn.addEventListener('click', function() {{
                filterBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentFilter = this.dataset.filter;
                filterTable();
            }});
        }});

        function filterTable() {{
            const searchTerm = searchInput.value.toLowerCase();
            const updatedRows = document.querySelectorAll('#updatedTable tbody tr');
            const originalRows = document.querySelectorAll('#originalTable tbody tr');

            let visibleCount = 0;
            let totalCount = 0;

            // Filter updated prompt table
            updatedRows.forEach(row => {{
                totalCount++;
                const modelName = row.cells[0].textContent.toLowerCase();
                const matchesSearch = modelName.includes(searchTerm);
                const matchesFilter = currentFilter === 'all' || currentFilter === 'updated';

                if (matchesSearch && matchesFilter) {{
                    row.classList.remove('hidden');
                    visibleCount++;
                }} else {{
                    row.classList.add('hidden');
                }}
            }});

            // Filter original prompt table
            originalRows.forEach(row => {{
                totalCount++;
                const modelName = row.cells[0].textContent.toLowerCase();
                const matchesSearch = modelName.includes(searchTerm);
                const matchesFilter = currentFilter === 'all' || currentFilter === 'original';

                if (matchesSearch && matchesFilter) {{
                    row.classList.remove('hidden');
                    visibleCount++;
                }} else {{
                    row.classList.add('hidden');
                }}
            }});

            // Update stats
            document.getElementById('visibleCount').textContent = visibleCount;
            document.getElementById('totalCount').textContent = totalCount;

            // Show/hide sections based on filter
            document.querySelectorAll('.section').forEach((section, index) => {{
                if (currentFilter === 'all') {{
                    section.style.display = 'block';
                }} else if (currentFilter === 'updated' && index === 0) {{
                    section.style.display = 'block';
                }} else if (currentFilter === 'original' && index === 1) {{
                    section.style.display = 'block';
                }} else {{
                    section.style.display = 'none';
                }}
            }});
        }}

        // Sorting functionality
        document.querySelectorAll('th[data-sort]').forEach(header => {{
            header.addEventListener('click', function() {{
                const table = this.closest('table');
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                const sortKey = this.dataset.sort;
                const columnIndex = Array.from(this.parentElement.children).indexOf(this);

                // Determine sort direction
                const isAscending = this.classList.contains('sort-asc');

                // Remove sort classes from all headers in this table
                table.querySelectorAll('th').forEach(th => {{
                    th.classList.remove('sort-asc', 'sort-desc');
                }});

                // Add appropriate class
                this.classList.add(isAscending ? 'sort-desc' : 'sort-asc');

                // Sort rows
                rows.sort((a, b) => {{
                    let aVal = a.cells[columnIndex].textContent;
                    let bVal = b.cells[columnIndex].textContent;

                    // Parse numbers
                    if (sortKey !== 'model') {{
                        aVal = parseFloat(aVal.replace('%', '')) || 0;
                        bVal = parseFloat(bVal.replace('%', '')) || 0;
                    }}

                    if (isAscending) {{
                        return aVal > bVal ? 1 : -1;
                    }} else {{
                        return aVal < bVal ? 1 : -1;
                    }}
                }});

                // Reorder rows in DOM
                rows.forEach(row => tbody.appendChild(row));
            }});
        }});

        // Initialize stats
        filterTable();
    </script>
</body>
</html>"""

    # Write the HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Leaderboard HTML generated at {output_path}")

if __name__ == "__main__":
    # Default paths, can be modified as needed
    summary_csv_path = "fundraising-emails/summary_all_json.csv"
    output_html_path = "fundraising-emails/index.html"
    generate_leaderboard_html(summary_csv_path, output_html_path)