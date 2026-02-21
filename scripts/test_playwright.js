const { chromium } = require('playwright');
(async () => {
  try {
    const browser = await chromium.launch();
    console.log('Browser launched successfully');
    await browser.close();
  } catch (error) {
    console.error('Launch failed:', error.message);
    process.exit(1);
  }
})();
