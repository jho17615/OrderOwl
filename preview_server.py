"""
OrderOwl 프론트엔드 프리뷰 서버
JSP → HTML 변환 + 더미 데이터 주입 후 정적 서버 실행
"""
import re, os, shutil
from http.server import HTTPServer, SimpleHTTPRequestHandler

SRC = r"C:\OrderOwl-main\OrderOwl\src\main\webapp"
DST = r"C:\OrderOwl-main\preview_html"

# ─────────────────────────────────────────────────────────────
# 더미 데이터 주입 스크립트 (JS: DOMContentLoaded 후 실행)
# ─────────────────────────────────────────────────────────────

MENU_LIST_INJECT = """
<script>
document.addEventListener('DOMContentLoaded', function() {
  var menus = [
    {id:1, name:'후라이드 치킨', price:'18,000원', desc:'바삭하고 담백한 후라이드'},
    {id:2, name:'양념 치킨',    price:'19,000원', desc:'달콤 매콤한 양념 소스'},
    {id:3, name:'간장 치킨',    price:'20,000원', desc:'깊은 풍미의 간장 소스'},
    {id:4, name:'콜라 (1.5L)', price:'3,000원',  desc:'시원한 탄산음료'},
    {id:5, name:'치킨무',       price:'1,000원',  desc:'새콤달콤 치킨무 서비스'},
  ];
  var table = document.querySelector('#list table');
  if (!table) return;
  menus.forEach(function(m) {
    var tr = document.createElement('tr');
    tr.innerHTML =
      '<td><button class="modalBtn">'+m.name+'</button></td>' +
      '<td>'+m.price+'</td>' +
      '<td>'+m.desc+'</td>' +
      '<td class="process">' +
        '<form><button type="button">삭제</button></form>' +
        '<form><button type="button">수정</button></form>' +
      '</td>';
    table.appendChild(tr);
  });
});
</script>
"""

ORDER_LIST_INJECT = """
<script>
document.addEventListener('DOMContentLoaded', function() {
  var orders = [
    {id:101, time:'12:35:04', price:'37,000원', table:'3번'},
    {id:102, time:'12:41:22', price:'19,000원', table:'1번'},
    {id:103, time:'13:02:11', price:'21,000원', table:'5번'},
    {id:104, time:'13:15:55', price:'18,000원', table:'2번'},
  ];
  var table = document.querySelector('#list table');
  if (!table) return;
  orders.forEach(function(o) {
    var tr = document.createElement('tr');
    tr.innerHTML =
      '<td>'+o.id+'</td>' +
      '<td>'+o.time+'</td>' +
      '<td>'+o.price+'</td>' +
      '<td>'+o.table+'</td>' +
      '<td class="process">' +
        '<button class="modalBtn" type="button">확인</button>' +
        '<form><button type="button">완료</button></form>' +
        '<form><button type="button">취소</button></form>' +
      '</td>';
    table.appendChild(tr);
  });
});
</script>
"""

QR_INJECT = """
<script>
document.addEventListener('DOMContentLoaded', function() {
  var qrs = [
    {no:'1번 테이블', id:1},
    {no:'2번 테이블', id:2},
    {no:'3번 테이블', id:3},
    {no:'VIP 룸',     id:4},
  ];
  var container = document.getElementById('qrMain');
  if (!container) return;
  qrs.forEach(function(q) {
    var url = 'http://localhost:8888/index.html?table='+q.id;
    var div = document.createElement('div');
    div.className = 'qrDiv';
    div.innerHTML =
      '<img src="https://api.qrserver.com/v1/create-qr-code/?size=120x120&data='+encodeURIComponent(url)+'" alt="QR">'+
      '<p>'+q.no+'</p>';
    container.appendChild(div);
  });
});
</script>
"""

# adminDashboard: DOM 직접 조작 + DOMContentLoaded 후 실행
ADMIN_AJAX_MOCK = """
<script>
// ── 프리뷰 Mock: DOM 직접 조작 ──────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  var stores = [
    {storeId:1, storeName:'올빼미 치킨',   region:'서울', ownerId:1, phoneNumber:'02-1234-5678', createdAt:'2025-01-15'},
    {storeId:2, storeName:'달빛 카페',     region:'부산', ownerId:2, phoneNumber:'051-234-5678', createdAt:'2025-02-20'},
    {storeId:3, storeName:'맛있는 분식',   region:'대구', ownerId:3, phoneNumber:'053-345-6789', createdAt:'2025-03-10'},
  ];
  var users = [
    {userId:1, username:'김철수', email:'kim@example.com', role:'USER', createdAt:'2025-01-10'},
    {userId:2, username:'이영희', email:'lee@example.com', role:'USER', createdAt:'2025-02-05'},
    {userId:3, username:'박민준', email:'park@example.com', role:'USER', createdAt:'2025-03-15'},
  ];
  var menus = [
    {menuId:1, menuName:'후라이드 치킨', price:18000, category1Code:1, checkRec:'Y', soldOut:'N'},
    {menuId:2, menuName:'양념 치킨',    price:19000, category1Code:1, checkRec:'N', soldOut:'N'},
    {menuId:3, menuName:'콜라',         price:3000,  category1Code:3, checkRec:'N', soldOut:'N'},
  ];

  // ── 대시보드 통계 ──
  var ss = document.getElementById('statStores');
  var su = document.getElementById('statUsers');
  if (ss) ss.textContent = stores.length;
  if (su) su.textContent = users.length;

  // ── 최근 매장 목록 ──
  var rsl = document.getElementById('recentStoreList');
  if (rsl) {
    var html = '<div class="space-y-2">';
    stores.forEach(function(s) {
      html += '<div class="flex justify-between items-center py-3 border-b">'
            + '<div><p class="font-medium">'+s.storeName+'</p>'
            + '<p class="text-sm text-gray-500">'+s.region+'</p></div>'
            + '<span class="text-sm text-gray-500">ID: '+s.storeId+'</span></div>';
    });
    html += '</div>';
    rsl.innerHTML = html;
  }

  // ── 매장 관리 테이블 ──
  var st = document.getElementById('storeTable');
  if (st) {
    var h = '';
    stores.forEach(function(s) {
      h += '<tr class="border-b hover:bg-gray-50">'
         + '<td class="px-6 py-4 font-medium">'+s.storeName+'</td>'
         + '<td class="px-6 py-4">'+s.ownerId+'</td>'
         + '<td class="px-6 py-4">'+s.region+'</td>'
         + '<td class="px-6 py-4">'+s.phoneNumber+'</td>'
         + '<td class="px-6 py-4">'+s.createdAt+'</td>'
         + '<td class="px-6 py-4"><div class="flex gap-2">'
         + '<button class="px-3 py-1.5 bg-blue-500 text-white rounded-lg text-sm">수정</button>'
         + '<button class="px-3 py-1.5 bg-red-500 text-white rounded-lg text-sm">삭제</button>'
         + '</div></td></tr>';
    });
    st.innerHTML = h;
  }

  // ── 유저 관리 테이블 ──
  var ut = document.getElementById('userTable');
  if (ut) {
    var hu = '';
    users.forEach(function(u) {
      hu += '<tr class="border-b hover:bg-gray-50">'
          + '<td class="px-6 py-4">'+u.userId+'</td>'
          + '<td class="px-6 py-4 font-medium">'+u.username+'</td>'
          + '<td class="px-6 py-4">'+u.email+'</td>'
          + '<td class="px-6 py-4"><span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">'+u.role+'</span></td>'
          + '<td class="px-6 py-4">'+u.createdAt+'</td>'
          + '<td class="px-6 py-4"><button class="px-3 py-1.5 bg-red-500 text-white rounded-lg text-sm">강제 탈퇴</button></td></tr>';
    });
    ut.innerHTML = hu;
  }

  // ── 메뉴 관리: 매장 select 채우기 ──
  var mss = document.getElementById('menuStoreSelect');
  var sss = document.getElementById('salesStoreSelect');
  var catNames = {1:'메인요리',2:'사이드',3:'음료',4:'디저트',5:'세트메뉴'};
  function fillStoreSelect(sel) {
    if (!sel) return;
    sel.innerHTML = '<option value="">매장을 선택하세요</option>';
    stores.forEach(function(s) {
      sel.innerHTML += '<option value="'+s.storeId+'">'+s.storeName+'</option>';
    });
  }
  fillStoreSelect(mss);
  fillStoreSelect(sss);

  // ── 메뉴 관리: 첫 번째 매장 메뉴 표시 ──
  var mtb = document.getElementById('menuTableBody');
  var mls = document.getElementById('menuListSection');
  if (mtb && mls) {
    var hm = '';
    menus.forEach(function(m) {
      var rec = m.checkRec==='Y' ? '<span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">추천</span>' : '';
      var so  = m.soldOut==='Y'  ? '<span class="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">품절</span>' : '';
      hm += '<tr class="border-t hover:bg-gray-50">'
          + '<td class="px-6 py-4 font-medium">'+m.menuName+'</td>'
          + '<td class="px-6 py-4">&#8361;'+m.price.toLocaleString()+'</td>'
          + '<td class="px-6 py-4">'+(catNames[m.category1Code]||'-')+'</td>'
          + '<td class="px-6 py-4">'+rec+'</td>'
          + '<td class="px-6 py-4">'+so+'</td>'
          + '<td class="px-6 py-4"><div class="flex gap-2">'
          + '<button class="px-3 py-1.5 bg-blue-500 text-white rounded-lg text-sm">수정</button>'
          + '<button class="px-3 py-1.5 bg-red-500 text-white rounded-lg text-sm">삭제</button>'
          + '</div></td></tr>';
    });
    mtb.innerHTML = hm;
    if (mss) mss.value = '1';
    mls.classList.remove('hidden');
  }

  // ── 매출 통계 ──
  var salesStat = document.getElementById('salesStats');
  if (salesStat) {
    var ts = document.getElementById('totalSales');
    var to = document.getElementById('totalOrders');
    var ao = document.getElementById('avgOrderAmount');
    if (ts) ts.textContent = '&#8361;1,250,000';
    if (to) to.textContent = '78';
    if (ao) ao.textContent = '&#8361;16,025';
    var dsl = document.getElementById('dailySalesList');
    if (dsl) {
      var days = [{d:'2025-05-29',t:220000},{d:'2025-05-30',t:165000},{d:'2025-05-31',t:310000},{d:'2025-06-01',t:370000},{d:'2025-06-02',t:185000}];
      var hd = '';
      days.forEach(function(x){ hd += '<div class="flex justify-between items-center p-3 border-b"><span>'+x.d+'</span><span class="font-semibold">&#8361;'+x.t.toLocaleString()+'</span></div>'; });
      dsl.innerHTML = hd;
    }
    if (salesStat) { salesStat.classList.remove('hidden'); if (sss) sss.value='1'; }
  }
});
// ────────────────────────────────────────────────────────────
</script>
"""

# inform 페이지: Java scriptlet을 더미 salesData로 교체
INFORM_SALES_DUMMY = """<script>
    const salesData = {"9":50000,"10":85000,"11":120000,"12":200000,"13":175000,"14":90000,"15":60000};
    const labels = Object.keys(salesData);
    const dataValues = Object.values(salesData);
    const state = "hour";
</script>"""

# inform 페이지: 매장 정보 표시
INFORM_STORE_INJECT = """
<script>
document.addEventListener('DOMContentLoaded', function() {
  var map = {
    'mainText': '매장이름 : 올빼미 치킨',
  };
  document.querySelectorAll('.mainText').forEach(function(el) {
    el.textContent = '매장이름 : 올빼미 치킨';
  });
  document.querySelectorAll('.subText').forEach(function(el, i) {
    var texts = ['주소 : 서울시 강남구 테헤란로 1', '지역 : 서울', '번호 : 02-1234-5678',
                 '매장 정보 : 바삭한 치킨 전문점', '이름 : 김철수'];
    if (texts[i]) el.textContent = texts[i];
  });
});
</script>
"""

# menu/update: 샘플 메뉴 데이터로 폼 채우기
MENU_UPDATE_INJECT = """
<script>
document.addEventListener('DOMContentLoaded', function() {
  var f = {
    name: '후라이드 치킨', price: 18000,
    description: '바삭하고 담백한 후라이드', src: '',
    cat1: 1, cat2: 2, checkRec: 'Y', soldOut: 'N', closeTime: '22:00'
  };
  var el = function(id) { return document.getElementById(id); };
  if (el('name')) el('name').value = f.name;
  if (el('price')) el('price').value = f.price;
  if (el('description')) el('description').value = f.description;
  if (el('src')) el('src').value = f.src;
  if (el('closeTime')) el('closeTime').value = f.closeTime;
  var r1 = document.querySelector('input[name="category1Code"][value="'+f.cat1+'"]');
  if (r1) r1.checked = true;
  var r2 = document.querySelector('input[name="category2Code"][value="'+f.cat2+'"]');
  if (r2) r2.checked = true;
  var rec = document.querySelector('input[name="checkRec"][value="'+f.checkRec+'"]');
  if (rec) rec.checked = true;
  var so = document.querySelector('input[name="soldOut"][value="'+f.soldOut+'"]');
  if (so) so.checked = true;
});
</script>
"""

# ─────────────────────────────────────────────────────────────
# 변환 함수
# ─────────────────────────────────────────────────────────────

def rel_prefix(rel_path):
    """상대 경로 깊이에 따라 contextPath 대체 문자열 계산"""
    depth = len(rel_path.replace('\\', '/').split('/')) - 1
    return '/'.join(['..'] * depth) if depth > 0 else '.'

def strip_jsp(content, ctx):
    """JSP 전용 구문 제거 및 경로 수정"""
    # 페이지 디렉티브
    content = re.sub(r'<%@\s*page[^%]*%>', '', content)
    # taglib 디렉티브
    content = re.sub(r'<%@\s*taglib[^%]*%>', '', content)
    # 자바 scriptlet (inform의 Gson 포함)
    content = re.sub(r'<%[^@][^%]*%>', '', content, flags=re.DOTALL)
    # JSTL forEach / if / otherwise 태그 제거 (내용 유지)
    content = re.sub(r'<c:forEach[^>]*>', '', content)
    content = re.sub(r'</c:forEach>', '', content)
    content = re.sub(r'<c:if[^>]*>', '', content)
    content = re.sub(r'</c:if>', '', content)
    content = re.sub(r'<c:otherwise[^>]*>', '', content)
    content = re.sub(r'</c:otherwise>', '', content)
    content = re.sub(r'<c:choose[^>]*>', '', content)
    content = re.sub(r'</c:choose>', '', content)
    content = re.sub(r'<c:when[^>]*>', '', content)
    content = re.sub(r'</c:when>', '', content)
    # contextPath EL
    content = re.sub(r'\$\{pageContext\.request\.contextPath\}', ctx, content)
    # 나머지 EL 표현식 → 빈 문자열로 (value 속성은 보존)
    content = re.sub(r'\s*=\s*"\$\{[^}]+\}"', '=""', content)
    content = re.sub(r'\$\{[^}]+\}', '', content)
    # .jsp 링크 → .html
    content = re.sub(r'\.jsp(["\'\s?#])', r'.html\1', content)
    # git conflict 마커 제거
    content = re.sub(r'<<<<<<< HEAD.*?>>>>>>> [^\n]+\n', '', content, flags=re.DOTALL)
    content = re.sub(r'=======\n.*?>>>>>>> [^\n]+\n', '', content, flags=re.DOTALL)
    content = re.sub(r'<<<<<<< HEAD\n|=======\n|>>>>>>> [^\n]+\n', '', content)
    return content

def inject_before_body_close(content, snippet):
    """</body> 직전에 스크립트 삽입"""
    return content.replace('</body>', snippet + '\n</body>', 1)

def inject_after_jquery(content, snippet):
    """jQuery 로드 이후(=</head> 직전)에 삽입 → admin 전용"""
    # jQuery 스크립트 태그 바로 뒤에 삽입
    return re.sub(
        r'(</head>)',
        snippet + r'\n\1',
        content, count=1
    )

PAGE_INJECTIONS = {
    # rel_path (슬래시 통일) → inject 함수 목록
    'user/menu/list/list':     [lambda c: inject_before_body_close(c, MENU_LIST_INJECT)],
    'user/order/order/order':  [lambda c: inject_before_body_close(c, ORDER_LIST_INJECT)],
    'user/qr/qr/qr':           [lambda c: inject_before_body_close(c, QR_INJECT)],
    'user/menu/update/update': [lambda c: inject_before_body_close(c, MENU_UPDATE_INJECT)],
    'user/inform/inform/inform': [
        # 1) scriptlet 제거 후 남은 깨진 JSON.parse('') 블록 제거
        lambda c: re.sub(r'<script>[^<]*JSON\.parse\([^<]*\)[^<]*</script>', '', c, flags=re.DOTALL),
        lambda c: re.sub(r'<script>\s*</script>', '', c),
        lambda c: c.replace('</head>', INFORM_SALES_DUMMY + '\n</head>', 1),
        lambda c: inject_before_body_close(c, INFORM_STORE_INJECT),
    ],
    'adminDashboard': [
        lambda c: inject_before_body_close(c, ADMIN_AJAX_MOCK),
    ],
}

def build_preview():
    if os.path.exists(DST):
        shutil.rmtree(DST)
    os.makedirs(DST)

    for root, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d not in ('WEB-INF', '.vscode')]

        rel_dir = os.path.relpath(root, SRC).replace('\\', '/')
        dst_dir = os.path.join(DST, rel_dir) if rel_dir != '.' else DST
        os.makedirs(dst_dir, exist_ok=True)

        for f in files:
            src_file = os.path.join(root, f)
            if f.endswith('.jsp'):
                # 변환 키 (확장자 제거, 슬래시)
                if rel_dir == '.':
                    key = f[:-4]
                else:
                    key = rel_dir + '/' + f[:-4]

                # contextPath 상대 경로
                ctx = rel_prefix(key)

                with open(src_file, encoding='utf-8', errors='ignore') as fh:
                    content = fh.read()

                content = strip_jsp(content, ctx)

                # 페이지별 주입
                for fn in PAGE_INJECTIONS.get(key, []):
                    content = fn(content)

                dst_file = os.path.join(dst_dir, f[:-4] + '.html')
                with open(dst_file, 'w', encoding='utf-8') as fh:
                    fh.write(content)

                print(f'  OK {key}.html')
            else:
                shutil.copy2(src_file, os.path.join(dst_dir, f))

    print('\nBuild done!')


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DST, **kwargs)
    def log_message(self, fmt, *args):
        pass


if __name__ == '__main__':
    print('빌드 중...')
    build_preview()
    port = 8888
    server = HTTPServer(('localhost', port), Handler)
    print(f'\n서버 실행 중: http://localhost:{port}')
    print('─' * 50)
    print('  로그인         http://localhost:8888/user/auth/login/login.html')
    print('  회원가입       http://localhost:8888/user/auth/account/account.html')
    print('  메뉴 목록      http://localhost:8888/user/menu/list/list.html')
    print('  메뉴 추가      http://localhost:8888/user/menu/insert/insert.html')
    print('  메뉴 수정      http://localhost:8888/user/menu/update/update.html')
    print('  주문 관리      http://localhost:8888/user/order/order/order.html')
    print('  매장 정보      http://localhost:8888/user/inform/inform/inform.html')
    print('  QR 관리        http://localhost:8888/user/qr/qr/qr.html')
    print('  관리자 대시보드 http://localhost:8888/adminDashboard.html')
    print('─' * 50)
    print('종료: Ctrl+C\n')
    server.serve_forever()
