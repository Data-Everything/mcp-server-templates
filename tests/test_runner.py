"""
Test runner and reporting utilities for comprehensive test execution.

Provides tools for running tests with coverage, generating reports,
and organizing test execution across different test categories.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class TestRunner:
    """Comprehensive test runner with coverage and reporting."""

    def __init__(self, root_dir: Optional[Path] = None):
        """Initialize test runner.

        Args:
            root_dir: Root directory of the project (defaults to current directory)
        """
        self.root_dir = root_dir or Path.cwd()
        self.test_dir = self.root_dir / "tests"
        self.coverage_dir = self.root_dir / "htmlcov"

    def run_quick_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run quick validation tests without coverage.

        Args:
            verbose: Whether to show verbose output

        Returns:
            Dict containing test results
        """
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_configuration.py",
            "--tb=short",
            "-x",  # Stop on first failure
            "--cov-fail-under=0",  # Don't fail on coverage
        ]

        if verbose:
            cmd.append("-v")

        return self._run_pytest(cmd, "Quick Tests")

    def run_unit_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run unit tests with coverage.

        Args:
            verbose: Whether to show verbose output

        Returns:
            Dict containing test results and coverage info
        """
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            "unit",
            "--cov=mcp_template",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
        ]

        if verbose:
            cmd.append("-v")

        return self._run_pytest(cmd, "Unit Tests")

    def run_integration_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run integration tests.

        Args:
            verbose: Whether to show verbose output

        Returns:
            Dict containing test results
        """
        cmd = [sys.executable, "-m", "pytest", "-m", "integration", "--tb=short"]

        if verbose:
            cmd.append("-v")

        return self._run_pytest(cmd, "Integration Tests")

    def run_docker_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run Docker-dependent tests.

        Args:
            verbose: Whether to show verbose output

        Returns:
            Dict containing test results
        """
        cmd = [sys.executable, "-m", "pytest", "-m", "docker", "--tb=short"]

        if verbose:
            cmd.append("-v")

        return self._run_pytest(cmd, "Docker Tests")

    def run_e2e_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run end-to-end tests.

        Args:
            verbose: Whether to show verbose output

        Returns:
            Dict containing test results
        """
        cmd = [sys.executable, "-m", "pytest", "-m", "e2e", "--tb=long"]

        if verbose:
            cmd.append("-v")

        return self._run_pytest(cmd, "End-to-End Tests")

    def run_template_tests(
        self, template_name: Optional[str] = None, verbose: bool = True
    ) -> Dict[str, Any]:
        """Run template-specific tests.

        Args:
            template_name: Specific template to test (None for all)
            verbose: Whether to show verbose output

        Returns:
            Dict containing test results
        """
        if template_name:
            test_path = f"templates/{template_name}/tests"
            cmd = [sys.executable, "-m", "pytest", test_path, "--tb=short"]
        else:
            cmd = [sys.executable, "-m", "pytest", "-m", "template", "--tb=short"]

        if verbose:
            cmd.append("-v")

        return self._run_pytest(cmd, f"Template Tests ({template_name or 'all'})")

    def run_all_tests(
        self,
        include_slow: bool = False,
        include_docker: bool = False,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """Run all tests with comprehensive coverage.

        Args:
            include_slow: Whether to include slow tests
            include_docker: Whether to include Docker-dependent tests
            verbose: Whether to show verbose output

        Returns:
            Dict containing comprehensive test results
        """
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--cov=mcp_template",
            "--cov=templates",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-fail-under=15",
        ]

        # Build marker expression
        markers = []
        if not include_slow:
            markers.append("not slow")
        if not include_docker:
            markers.append("not docker")

        if markers:
            cmd.extend(["-m", " and ".join(markers)])

        if verbose:
            cmd.append("-v")

        return self._run_pytest(cmd, "All Tests")

    def run_specific_test_file(
        self, test_file: str, verbose: bool = True
    ) -> Dict[str, Any]:
        """Run a specific test file.

        Args:
            test_file: Path to the test file
            verbose: Whether to show verbose output

        Returns:
            Dict containing test results
        """
        cmd = [sys.executable, "-m", "pytest", test_file, "--tb=short"]

        if verbose:
            cmd.append("-v")

        return self._run_pytest(cmd, f"Test File: {test_file}")

    def run_coverage_only(self) -> Dict[str, Any]:
        """Run tests purely for coverage measurement.

        Returns:
            Dict containing coverage results
        """
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--cov=mcp_template",
            "--cov=templates",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
            "--quiet",
            "-x",  # Stop on first failure
        ]

        return self._run_pytest(cmd, "Coverage Analysis")

    def generate_coverage_report(self) -> Path:
        """Generate detailed coverage report.

        Returns:
            Path to the generated HTML coverage report
        """
        # Run coverage
        subprocess.run(
            [
                sys.executable,
                "-m",
                "coverage",
                "html",
                "--directory",
                str(self.coverage_dir),
            ],
            check=True,
        )

        return self.coverage_dir / "index.html"

    def check_test_quality(self) -> Dict[str, Any]:
        """Check test quality metrics.

        Returns:
            Dict containing quality metrics
        """
        metrics = {
            "test_files": len(list(self.test_dir.glob("**/test_*.py"))),
            "test_coverage": self._get_coverage_percentage(),
            "missing_tests": self._find_missing_tests(),
            "duplicate_tests": self._find_duplicate_tests(),
        }

        return metrics

    def _run_pytest(self, cmd: List[str], test_type: str) -> Dict[str, Any]:
        """Run pytest command and capture results.

        Args:
            cmd: Command to run
            test_type: Type of tests being run

        Returns:
            Dict containing test results
        """
        print(f"\n=== Running {test_type} ===")
        print(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            return {
                "test_type": test_type,
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": cmd,
            }

        except subprocess.TimeoutExpired:
            return {
                "test_type": test_type,
                "success": False,
                "return_code": -1,
                "error": "Test execution timed out",
                "command": cmd,
            }
        except Exception as e:
            return {
                "test_type": test_type,
                "success": False,
                "return_code": -1,
                "error": str(e),
                "command": cmd,
            }

    def _get_coverage_percentage(self) -> Optional[float]:
        """Get current test coverage percentage.

        Returns:
            Coverage percentage or None if not available
        """
        coverage_file = self.root_dir / "coverage.xml"
        if not coverage_file.exists():
            return None

        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(coverage_file)
            root = tree.getroot()

            coverage_elem = root.find(".//coverage")
            if coverage_elem is not None:
                return float(coverage_elem.get("line-rate", 0)) * 100

        except Exception:
            pass

        return None

    def _find_missing_tests(self) -> List[str]:
        """Find source files that don't have corresponding tests.

        Returns:
            List of source files missing tests
        """
        missing_tests = []

        # Check mcp_template module
        mcp_template_dir = self.root_dir / "mcp_template"
        if mcp_template_dir.exists():
            for py_file in mcp_template_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue

                test_file = self.test_dir / f"test_{py_file.stem}.py"
                if not test_file.exists():
                    missing_tests.append(str(py_file.relative_to(self.root_dir)))

        return missing_tests

    def _find_duplicate_tests(self) -> List[str]:
        """Find potentially duplicate test functions.

        Returns:
            List of potentially duplicate tests
        """
        test_names = {}
        duplicates = []

        for test_file in self.test_dir.glob("**/test_*.py"):
            try:
                content = test_file.read_text()
                for line_num, line in enumerate(content.split("\n"), 1):
                    if line.strip().startswith("def test_"):
                        test_name = line.split("(")[0].replace("def ", "")

                        if test_name in test_names:
                            duplicates.append(
                                f"{test_name} in {test_file} and {test_names[test_name]}"
                            )
                        else:
                            test_names[test_name] = f"{test_file}:{line_num}"

            except Exception:
                continue

        return duplicates


def main():
    """Main function for running tests from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Run MCP Template tests")
    parser.add_argument(
        "--quick", action="store_true", help="Run quick validation tests only"
    )
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )
    parser.add_argument("--docker", action="store_true", help="Run Docker tests only")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests only")
    parser.add_argument("--template", help="Run tests for specific template")
    parser.add_argument("--file", help="Run specific test file")
    parser.add_argument(
        "--coverage", action="store_true", help="Run coverage analysis only"
    )
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument(
        "--include-slow", action="store_true", help="Include slow tests"
    )
    parser.add_argument(
        "--include-docker", action="store_true", help="Include Docker tests"
    )
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    parser.add_argument(
        "--quality", action="store_true", help="Check test quality metrics"
    )

    args = parser.parse_args()

    runner = TestRunner()
    verbose = not args.quiet

    results = []

    if args.quick:
        results.append(runner.run_quick_tests(verbose))
    elif args.unit:
        results.append(runner.run_unit_tests(verbose))
    elif args.integration:
        results.append(runner.run_integration_tests(verbose))
    elif args.docker:
        results.append(runner.run_docker_tests(verbose))
    elif args.e2e:
        results.append(runner.run_e2e_tests(verbose))
    elif args.template:
        results.append(runner.run_template_tests(args.template, verbose))
    elif args.file:
        results.append(runner.run_specific_test_file(args.file, verbose))
    elif args.coverage:
        results.append(runner.run_coverage_only())
    elif args.quality:
        metrics = runner.check_test_quality()
        print("\n=== Test Quality Metrics ===")
        for key, value in metrics.items():
            print(f"{key}: {value}")
        return
    elif args.all:
        results.append(
            runner.run_all_tests(args.include_slow, args.include_docker, verbose)
        )
    else:
        # Default: run all tests excluding slow and docker
        results.append(runner.run_all_tests(False, False, verbose))

    # Print results summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    total_success = True
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{result['test_type']}: {status}")
        if not result["success"]:
            total_success = False
            print(f"  Return code: {result['return_code']}")
            if "error" in result:
                print(f"  Error: {result['error']}")

    print("=" * 60)
    overall_status = "✅ ALL TESTS PASSED" if total_success else "❌ SOME TESTS FAILED"
    print(f"OVERALL: {overall_status}")

    sys.exit(0 if total_success else 1)


if __name__ == "__main__":
    main()
