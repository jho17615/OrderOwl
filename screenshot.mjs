import puppeteer from 'puppeteer';
import path from 'path';

const DESKTOP = 'C:\\Users\\jho17\\OneDrive\\바탕 화면';
const BASE = 'http://localhost:8888';

const pages = [
  { name: '01_로그인',           url: '/user/auth/login/login.html' },
  { name: '02_회원가입',         url: '/user/auth/account/account.html' },
  { name: '03_메뉴목록',         url: '/user/menu/list/list.html' },
  { name: '04_메뉴추가',         url: '/user/menu/insert/insert.html' },
  { name: '05_메뉴수정',         url: '/user/menu/update/update.html' },
  { name: '06_주문관리',         url: '/user/order/order/order.html' },
  { name: '07_매장정보_매출통계', url: '/user/inform/inform/inform.html' },
  { name: '08_QR관리',           url: '/user/qr/qr/qr.html' },
  { name: '09_관리자대시보드',    url: '/adminDashboard.html' },
  { name: '10_고객주문페이지',    url: '/index.html' },
];

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  for (const p of pages) {
    try {
      await page.goto(BASE + p.url, { waitUntil: 'networkidle0', timeout: 15000 });
      // DOMContentLoaded 이후 주입 스크립트가 실행될 시간 대기
      await new Promise(r => setTimeout(r, 1200));
      const file = path.join(DESKTOP, p.name + '.png');
      await page.screenshot({ path: file, fullPage: true });
      console.log('saved: ' + p.name + '.png');
    } catch (e) {
      console.log('FAIL ' + p.name + ': ' + e.message);
    }
  }

  await browser.close();
  console.log('\n완료! 바탕화면에 저장됨.');
})();
