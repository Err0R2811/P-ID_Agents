async (page) => {
  const fs = await import('fs');
  const path = await import('path');
  const pdfPath = 'c:/Users/amitv/Desktop/PHA-Pro/PDF/123.pdf';
  const apiKey = 'sk-WdEu3IsubI64Ew9BSme7rTF6QOcpGZMn1EgnsCdb7uXOZ0Es';
  const outDir = 'c:/Users/amitv/Desktop/PHA-Pro/PDF/output/rendered';
  fs.mkdirSync(outDir, { recursive: true });
  const screenshotPath = outDir + '/page_1.png';

  await page.goto('file:///' + pdfPath.replace(/\\/g, '/'), { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const imageB64 = fs.readFileSync(screenshotPath).toString('base64');

  const resp = await fetch('https://apihub.agnes-ai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: 'Bearer ' + apiKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'agnes-2.5-flash',
      temperature: 0.1,
      messages: [
        {
          role: 'system',
          content: 'You are a P&ID expert. Extract equipment, instruments, valves, connections from the drawing. NEVER invent tags. Return ONLY valid JSON: {entities, associations, connections, notes}.',
        },
        {
          role: 'user',
          content: [
            {
              type: 'text',
              text: 'Analyze this Lube Oil System P&ID for Compressor K-01. Extract all tags and connections with confidence scores. JSON only.',
            },
            {
              type: 'image_url',
              image_url: { url: 'data:image/png;base64,' + imageB64, detail: 'high' },
            },
          ],
        },
      ],
    }),
  });

  const text = await resp.text();
  fs.writeFileSync(
    'c:/Users/amitv/Desktop/PHA-Pro/PDF/output/llm_raw_response.json',
    JSON.stringify({ status: resp.status, screenshot: screenshotPath, response: text }, null, 2)
  );
  return { status: resp.status, screenshot: screenshotPath, preview: text.slice(0, 3000) };
}
