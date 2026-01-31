#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2025 Róbert Malovec
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Parse coverage XML and generate GitHub Actions summary table."""

import xml.etree.ElementTree as ET
import os


def write_to_summary(content):
    """Write content to GitHub Actions step summary."""
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
        f.write(content)


def main():
    try:
        tree = ET.parse('coverage.xml')
        root = tree.getroot()

        # Get overall coverage
        coverage_elem = root.find('.//coverage')
        if coverage_elem is not None:
            line_rate = float(coverage_elem.get('line-rate', 0)) * 100
            branch_rate = float(coverage_elem.get('branch-rate', 0)) * 100

            # Overall coverage table
            write_to_summary('### 🎯 Overall Coverage Summary\n\n')
            write_to_summary('| Coverage Type | Percentage | Status | Badge |\n')
            write_to_summary('|---------------|------------|--------|-------|\n')

            # Line coverage status
            if line_rate >= 90:
                line_status = '🟢 Excellent'
                line_badge = f'![Coverage](https://img.shields.io/badge/coverage-{line_rate:.1f}%25-brightgreen)'
            elif line_rate >= 80:
                line_status = '🟡 Good'
                line_badge = f'![Coverage](https://img.shields.io/badge/coverage-{line_rate:.1f}%25-green)'
            elif line_rate >= 70:
                line_status = '🟠 Fair'
                line_badge = f'![Coverage](https://img.shields.io/badge/coverage-{line_rate:.1f}%25-yellow)'
            elif line_rate >= 60:
                line_status = '🔴 Poor'
                line_badge = f'![Coverage](https://img.shields.io/badge/coverage-{line_rate:.1f}%25-orange)'
            else:
                line_status = '🔴 Critical'
                line_badge = f'![Coverage](https://img.shields.io/badge/coverage-{line_rate:.1f}%25-red)'

            write_to_summary(f'| **Line Coverage** | {line_rate:.1f}% | {line_status} | {line_badge} |\n')

            # Branch coverage status
            if branch_rate >= 80:
                branch_status = '🟢 Good'
            elif branch_rate >= 60:
                branch_status = '🟡 Fair'
            else:
                branch_status = '🔴 Needs Work'

            write_to_summary(f'| **Branch Coverage** | {branch_rate:.1f}% | {branch_status} | - |\n')
            write_to_summary('\n')

        # Per-file coverage table
        packages = root.findall('.//package')
        if packages:
            write_to_summary('### 📁 Coverage by Module\n\n')
            write_to_summary('| Module | Line Coverage | Lines Covered | Total Lines | Status |\n')
            write_to_summary('|--------|---------------|---------------|-------------|--------|\n')

            module_data = []
            for package in packages:
                classes = package.findall('.//class')
                for cls in classes:
                    filename = cls.get('filename', 'Unknown')
                    line_rate = float(cls.get('line-rate', 0)) * 100

                    # Count lines
                    lines = cls.findall('.//line')
                    total_lines = len(lines)
                    covered_lines = len([line for line in lines if line.get('hits', '0') != '0'])

                    # Get module name from filename
                    module_name = filename.replace('epg_grabber/', '').replace('.py', '').replace('/', '.')

                    # Status based on coverage
                    if line_rate >= 90:
                        status = '🟢 Excellent'
                    elif line_rate >= 80:
                        status = '🟡 Good'
                    elif line_rate >= 70:
                        status = '🟠 Fair'
                    elif line_rate >= 50:
                        status = '🔴 Poor'
                    else:
                        status = '🔴 Critical'

                    module_data.append((module_name, line_rate, covered_lines, total_lines, status))

            # Sort by coverage percentage (lowest first to highlight issues)
            module_data.sort(key=lambda x: x[1])

            for module_name, line_rate, covered_lines, total_lines, status in module_data:
                write_to_summary(f'| `{module_name}` | {line_rate:.1f}% | {covered_lines} | {total_lines} | {status} |\n')

            write_to_summary('\n')

            # Coverage recommendations
            low_coverage_modules = [m for m in module_data if m[1] < 80]
            if low_coverage_modules:
                write_to_summary('### 📋 Coverage Recommendations\n\n')
                write_to_summary('The following modules could benefit from additional test coverage:\n\n')
                for module_name, line_rate, covered_lines, total_lines, status in low_coverage_modules[:5]:
                    missing_lines = total_lines - covered_lines
                    write_to_summary(f'- **`{module_name}`**: {line_rate:.1f}% coverage ({missing_lines} lines need tests)\n')

                if len(low_coverage_modules) > 5:
                    write_to_summary(f'- ... and {len(low_coverage_modules) - 5} more modules\n')

                write_to_summary('\n')

    except FileNotFoundError:
        write_to_summary('### 📈 Coverage Report\n\n')
        write_to_summary('⚠️ **Coverage report not found** - Coverage may not have been generated\n\n')
    except ET.ParseError:
        write_to_summary('### 📈 Coverage Report\n\n')
        write_to_summary('⚠️ **Invalid coverage XML format** - Could not parse coverage report\n\n')
    except Exception as e:
        write_to_summary('### 📈 Coverage Report\n\n')
        write_to_summary(f'⚠️ **Error parsing coverage report:** {str(e)}\n\n')


if __name__ == '__main__':
    main()
