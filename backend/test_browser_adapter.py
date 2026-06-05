"""
Browser Adapter Validation Tests

Tests the browser abstraction layer:
- Adapter interface
- Mock implementation
- Page operations
- Element operations
- Result objects
- Lifecycle management
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.browser.adapter import MockBrowserAdapter
from backend.browser.page import BrowserPage
from backend.browser.element import BrowserElement
from backend.browser.result import BrowserResult


async def test_adapter_lifecycle():
    """Test 1: Adapter lifecycle (start/stop)."""
    print("\n=== Test 1: Adapter Lifecycle ===\n")

    try:
        adapter = MockBrowserAdapter()

        print("✓ Starting adapter")
        result = await adapter.start()
        assert result.success == True
        assert adapter.is_started == True
        print(f"  - {result}")

        print("✓ Stopping adapter")
        result = await adapter.stop()
        assert result.success == True
        assert adapter.is_started == False
        print(f"  - {result}")

        print("✅ Adapter lifecycle working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_navigation():
    """Test 2: Navigation (goto, current_url, get_title)."""
    print("\n=== Test 2: Navigation ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()

        url = "https://www.linkedin.com/jobs/view/123"
        print(f"✓ Navigating to {url}")
        result = await adapter.goto(url)
        assert result.success == True
        print(f"  - {result}")

        print("✓ Getting current URL")
        current = await adapter.current_url()
        assert current == url
        print(f"  - {current}")

        print("✓ Getting page title")
        title = await adapter.get_title()
        assert title != ""
        print(f"  - {title}")

        print("✅ Navigation working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_page_creation():
    """Test 3: Page object creation."""
    print("\n=== Test 3: Page Creation ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()
        await adapter.goto("https://example.com")

        print("✓ Getting page object")
        page = await adapter.get_page()
        assert isinstance(page, BrowserPage)
        print(f"  - {page}")

        print("✓ Extracting page metadata")
        metadata = page.extract_metadata()
        assert "url" in metadata
        assert "title" in metadata
        assert "loaded_at" in metadata
        print(f"  - URL: {metadata['url']}")
        print(f"  - Title: {metadata['title']}")

        print("✓ Extracting page HTML")
        html = page.extract_html()
        assert html != ""
        print(f"  - HTML length: {len(html)}")

        print("✅ Page creation working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_element_lookup():
    """Test 4: Element lookup (find_element, find_elements)."""
    print("\n=== Test 4: Element Lookup ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()
        await adapter.goto("https://example.com")

        selector = "input[name='firstName']"
        print(f"✓ Finding single element: {selector}")
        element = await adapter.find_element(selector)
        assert element is not None
        assert isinstance(element, BrowserElement)
        print(f"  - {element}")

        print("✓ Finding multiple elements")
        elements = await adapter.find_elements(selector)
        assert len(elements) > 0
        print(f"  - Found {len(elements)} element(s)")

        print("✓ Finding non-existent element")
        element = await adapter.find_element("nonexistent")
        assert element is not None  # Mock creates on demand
        print(f"  - {element}")

        print("✅ Element lookup working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_element_click():
    """Test 5: Element click simulation."""
    print("\n=== Test 5: Element Click ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()
        await adapter.goto("https://example.com")

        selector = "button[type='submit']"
        print(f"✓ Finding element: {selector}")
        element = await adapter.find_element(selector)
        assert element is not None

        print("✓ Clicking element")
        result = element.click()
        assert result.success == True
        assert result.action == "click"
        print(f"  - {result}")

        print("✓ Clicking hidden element")
        element.visible = False
        result = element.click()
        assert result.success == False
        print(f"  - {result}")

        print("✅ Element click working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_element_fill():
    """Test 6: Element fill simulation."""
    print("\n=== Test 6: Element Fill ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()
        await adapter.goto("https://example.com")

        selector = "input[name='email']"
        print(f"✓ Finding element: {selector}")
        element = await adapter.find_element(selector)
        assert element is not None

        value = "user@example.com"
        print(f"✓ Filling element with: {value}")
        result = element.fill(value)
        assert result.success == True
        assert result.action == "fill"
        print(f"  - {result}")

        print("✓ Verifying filled value")
        stored_value = element.get_attribute("value")
        assert stored_value == value
        print(f"  - Stored value: {stored_value}")

        print("✓ Filling hidden element")
        element.visible = False
        result = element.fill("should_fail")
        assert result.success == False
        print(f"  - {result}")

        print("✅ Element fill working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_result_objects():
    """Test 7: BrowserResult objects."""
    print("\n=== Test 7: Result Objects ===\n")

    try:
        print("✓ Creating success result")
        result = BrowserResult(
            success=True,
            action="click",
            selector="button",
            message="Clicked button",
            metadata={"timestamp": "2026-06-04T20:59:22Z"},
        )
        assert result.success == True
        print(f"  - {result}")

        print("✓ Creating failure result")
        result = BrowserResult(
            success=False,
            action="fill",
            selector="input",
            message="Element not visible",
        )
        assert result.success == False
        print(f"  - {result}")

        print("✓ Converting to dictionary")
        result_dict = result.to_dict()
        assert "success" in result_dict
        assert "action" in result_dict
        print(f"  - Keys: {list(result_dict.keys())}")

        print("✅ Result objects working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_wait_for_element():
    """Test 8: Wait for element."""
    print("\n=== Test 8: Wait for Element ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()
        await adapter.goto("https://example.com")

        selector = "div.dynamic-content"
        print(f"✓ Waiting for element: {selector}")
        element = await adapter.wait_for_element(selector, timeout=5)
        assert element is not None
        print(f"  - {element}")

        print("✅ Wait for element working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_screenshot():
    """Test 9: Screenshot operation."""
    print("\n=== Test 9: Screenshot ===\n")

    try:
        adapter = MockBrowserAdapter()
        await adapter.start()
        await adapter.goto("https://example.com")

        path = "/tmp/screenshot.png"
        print(f"✓ Taking screenshot to {path}")
        result = await adapter.screenshot(path)
        assert result.success == True
        print(f"  - {result}")

        print("✅ Screenshot working")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("BROWSER ABSTRACTION LAYER VALIDATION")
    print("="*70)

    results = {}

    results["lifecycle"] = await test_adapter_lifecycle()
    results["navigation"] = await test_navigation()
    results["page_creation"] = await test_page_creation()
    results["element_lookup"] = await test_element_lookup()
    results["element_click"] = await test_element_click()
    results["element_fill"] = await test_element_fill()
    results["result_objects"] = await test_result_objects()
    results["wait_for_element"] = await test_wait_for_element()
    results["screenshot"] = await test_screenshot()

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n" + "="*70)
        print("✅ BROWSER ABSTRACTION LAYER COMPLETE")
        print("="*70)
        print("\nCapabilities validated:")
        print("  ✅ Adapter lifecycle (start/stop)")
        print("  ✅ Navigation (goto, current_url, get_title)")
        print("  ✅ Page object creation")
        print("  ✅ Element lookup (single/multiple)")
        print("  ✅ Element interaction (click, fill)")
        print("  ✅ Result objects")
        print("  ✅ Wait for element")
        print("  ✅ Screenshots")
        print("\nReady for:")
        print("  • Playwright integration (Phase 5.6)")
        print("  • Selenium integration (future)")
        print("  • ExecutionEngine integration")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


def main():
    """Main entry point."""
    return asyncio.run(run_all_tests())


if __name__ == "__main__":
    sys.exit(main())
