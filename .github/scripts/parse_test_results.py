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

"""Parse pytest JSON results and generate GitHub Actions summary table."""

import json
import os


def write_to_summary(content):
    """Write content to GitHub Actions step summary."""
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
        f.write(content)


def main():
    try:
        # Parse test results JSON
        with open('test-results.json', 'r') as f:
            results = json.load(f)

        # Extract summary data
        summary = results.get('summary', {})
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        errors = summary.get('error', 0)
        duration = results.get('duration', 0)

        # Calculate percentages
        pass_rate = (passed / total * 100) if total > 0 else 0
        fail_rate = (failed / total * 100) if total > 0 else 0
        skip_rate = (skipped / total * 100) if total > 0 else 0
        error_rate = (errors / total * 100) if total > 0 else 0

        # Write test summary table
        write_to_summary('\n### 📊 Test Results Summary\n\n')
        write_to_summary('| Metric | Count | Percentage | Status |\n')
        write_to_summary('|--------|-------|------------|--------|\n')
        write_to_summary(f'| **Total Tests** | {total} | 100.0% | ℹ️ Info |\n')

        if passed > 0:
            write_to_summary(f'| **✅ Passed** | {passed} | {pass_rate:.1f}% | 🟢 Success |\n')
        else:
            write_to_summary(f'| **✅ Passed** | {passed} | {pass_rate:.1f}% | ⚪ None |\n')

        if failed > 0:
            write_to_summary(f'| **❌ Failed** | {failed} | {fail_rate:.1f}% | 🔴 Critical |\n')
        else:
            write_to_summary(f'| **❌ Failed** | {failed} | {fail_rate:.1f}% | ✅ Good |\n')

        if skipped > 0:
            write_to_summary(f'| **⏭️ Skipped** | {skipped} | {skip_rate:.1f}% | 🟡 Review |\n')
        else:
            write_to_summary(f'| **⏭️ Skipped** | {skipped} | {skip_rate:.1f}% | ✅ None |\n')

        if errors > 0:
            write_to_summary(f'| **💥 Errors** | {errors} | {error_rate:.1f}% | 🔴 Critical |\n')
        else:
            write_to_summary(f'| **💥 Errors** | {errors} | {error_rate:.1f}% | ✅ Good |\n')

        write_to_summary(f'| **⏱️ Duration** | {duration:.2f}s | - | ⏱️ Time |\n')
        write_to_summary('\n')

        # Overall status
        if failed > 0 or errors > 0:
            write_to_summary('🔴 **Overall Status: FAILED** - Tests need attention\n\n')
        elif skipped > 0:
            write_to_summary('🟡 **Overall Status: PASSED WITH SKIPS** - Review skipped tests\n\n')
        else:
            write_to_summary('🟢 **Overall Status: PASSED** - All tests successful\n\n')

        # Test details by file/module
        tests = results.get('tests', [])
        if tests:
            # Group tests by file
            test_files = {}
            for test in tests:
                nodeid = test.get('nodeid', '')
                file_path = nodeid.split('::')[0] if '::' in nodeid else 'unknown'
                if file_path not in test_files:
                    test_files[file_path] = {'passed': 0, 'failed': 0, 'skipped': 0, 'error': 0}

                outcome = test.get('outcome', 'unknown')
                if outcome in test_files[file_path]:
                    test_files[file_path][outcome] += 1

            write_to_summary('### 📁 Test Results by Module\n\n')
            write_to_summary('| Test File | ✅ Passed | ❌ Failed | ⏭️ Skipped | 💥 Errors | Status |\n')
            write_to_summary('|-----------|----------|----------|-----------|----------|--------|\n')

            for file_path, counts in sorted(test_files.items()):
                total_file = sum(counts.values())
                if total_file > 0:
                    file_name = file_path.replace('tests/', '').replace('.py', '')
                    status = '🟢 Pass' if counts['failed'] == 0 and counts['error'] == 0 else '🔴 Fail'
                    write_to_summary(f'| `{file_name}` | {counts["passed"]} | {counts["failed"]} | {counts["skipped"]} | {counts["error"]} | {status} |\n')

            write_to_summary('\n')

        # Show failed tests details if any
        failed_tests = [test for test in tests if test.get('outcome') in ['failed', 'error']]
        if failed_tests:
            write_to_summary('### ❌ Failed Tests Details\n\n')
            write_to_summary('| Test Name | File | Outcome | Duration |\n')
            write_to_summary('|-----------|------|---------|----------|\n')

            for test in failed_tests[:10]:  # Show first 10 failed tests
                nodeid = test.get('nodeid', '')
                test_name = nodeid.split('::')[-1] if '::' in nodeid else nodeid
                file_path = nodeid.split('::')[0] if '::' in nodeid else 'unknown'
                outcome = test.get('outcome', 'unknown')
                duration = test.get('duration', 0)

                outcome_emoji = '❌' if outcome == 'failed' else '💥'
                write_to_summary(f'| `{test_name}` | `{file_path}` | {outcome_emoji} {outcome} | {duration:.3f}s |\n')

            if len(failed_tests) > 10:
                write_to_summary(f'\n_... and {len(failed_tests) - 10} more failed tests. See full report in artifacts._\n')

            write_to_summary('\n')

    except FileNotFoundError:
        write_to_summary('\n### 📊 Test Results Summary\n\n')
        write_to_summary('⚠️ **Test results file not found** - Tests may not have run properly\n\n')
    except json.JSONDecodeError:
        write_to_summary('\n### 📊 Test Results Summary\n\n')
        write_to_summary('⚠️ **Invalid test results format** - Could not parse JSON\n\n')
    except Exception as e:
        write_to_summary('\n### 📊 Test Results Summary\n\n')
        write_to_summary(f'⚠️ **Error parsing test results:** {str(e)}\n\n')


if __name__ == '__main__':
    main()
