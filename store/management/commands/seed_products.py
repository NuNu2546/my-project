"""
Management command: seed_products
Seeds all 42 products from the original hardcoded list into the Product DB,
preserving original IDs so existing OrderItems and localStorage carts stay valid.
Safe to re-run: uses update_or_create.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from store.models import Product

PRODUCTS = [
    # ── เครื่องมือทำสวน (tools) ──────────────────────────────────────────────
    {'id': 1,  'name': 'บัวรดน้ำ',             'price': '6.00',  'category': 'tools',
     'image': 'images/grow_kits/watering_can.png',
     'description': '🚿 บัวรดน้ำคุณภาพสูง\n• ดีไซน์จับถนัดมือ รดน้ำได้แม่นยำ\n• วัสดุทนทาน ทนแดดทนฝน\n• อัตราการไหลของน้ำสม่ำเสมอ เหมาะสำหรับพืชทุกชนิด'},
    {'id': 2,  'name': 'ถุงขยะสวน',            'price': '6.00',  'category': 'tools',
     'image': 'images/grow_kits/garden_waste_bags.png',
     'description': '🗑️ ถุงขยะสวนเอนกประสงค์\n• จุของได้เยอะ เหมาะสำหรับเศษใบไม้และกิ่งไม้\n• วัสดุเหนียวพิเศษ ไม่ขาดง่าย\n• พับเก็บได้ ประหยัดพื้นที่ และทำความสะอาดง่าย'},
    {'id': 3,  'name': 'ป้ายชื่อต้นไม้',        'price': '2.00',  'category': 'tools',
     'image': 'images/grow_kits/plant_labels.png',
     'description': '🏷️ ป้ายชื่อต้นไม้\n• ช่วยจัดระเบียบสวนให้ดูเป็นมืออาชีพ\n• เขียนง่าย ติดทนนาน ไม่หลุดลอกง่าย\n• ทนต่อความชื้นและแสงแดด'},
    {'id': 4,  'name': 'กระถาง & ถาดเพาะเมล็ด', 'price': '2.00',  'category': 'tools',
     'image': 'images/grow_kits/pots_and_seed_trays.png',
     'description': '🌱 ชุดเริ่มต้นความสุข: กระถาง & ถาดเพาะเมล็ด\n• ดีไซน์มินิมอล: กระถางโทนสีอิฐธรรมชาติ เข้าได้กับทุกมุมในบ้าน\n• ฟังก์ชันครบ: มีทั้งถาดหลุมสำหรับเพาะกล้าและกระถางหลายขนาด\n• คุณภาพพรีเมียม: วัสดุแข็งแรง ระบายน้ำและอากาศได้ดี ช่วยให้รากเดินสะดวก'},
    {'id': 5,  'name': 'สายยางพร้อมหัวฉีด',     'price': '12.00', 'category': 'tools',
     'image': 'images/grow_kits/hose_with_spray_nozzle.png',
     'description': '🚿 สายยางพร้อมหัวฉีดดีไซน์พรีเมียม\n• หัวฉีดละอองละเอียด: ถนอมต้นกล้าและหน้าดิน ไม่ให้กระจายตัวแรง\n• สายยางคุณภาพสูง: ยืดหยุ่นได้ดี ไม่พันกัน และทนทานต่อแรงดันน้ำ\n• ด้ามจับลายไม้: สวยงามคลาสสิก และช่วยให้จับกระชับมือยิ่งขึ้น'},
    {'id': 6,  'name': 'กรรไกรตัดกิ่งยาว',      'price': '20.00', 'category': 'tools',
     'image': 'images/grow_kits/long_handle_pruning_shears.png',
     'description': '✂️ กรรไกรตัดกิ่งพรีเมียม: คมกริบ ผ่อนแรง\n• ใบมีดเหล็กคุณภาพสูง: ตัดกิ่งได้เรียบเนียน ไม่ทำให้เนื้อไม้ช้ำ\n• ระบบสปริงนุ่มนวล: ช่วยผ่อนแรงในทุกการตัด ลดความเมื่อยล้า\n• ด้ามจับลายไม้: ดีไซน์สวยงามตามหลักสรีรศาสตร์ จับถนัดมือ'},
    {'id': 7,  'name': 'พลั่ว',                  'price': '20.00', 'category': 'tools',
     'image': 'images/grow_kits/garden_shovel.png',
     'description': '⛏️ พลั่วตักดินพรีเมียม: แข็งแกร่ง ทนทาน\n• วัสดุสเตนเลส: ผิวมันเงา ไม่เป็นสนิมง่าย แข็งแรงทนทาน\n• ด้ามจับตัว Y: ออกแบบให้รับกับแรงกด ช่วยให้ขุดหรือตักดินได้ง่าย\n• เอนกประสงค์: เหมาะทั้งการขุดหลุมปลูก ย้ายต้นกล้า หรือผสมดิน'},
    {'id': 8,  'name': 'คราด',                   'price': '20.00', 'category': 'tools',
     'image': 'images/grow_kits/garden_rake.png',
     'description': '🍂 คราดพรวนดินพรีเมียม: เตรียมหน้าดินให้พร้อม\n• ซี่คราดเหล็กกล้า: ตะกุยดินที่จับตัวเป็นก้อนให้ร่วนซุยได้อย่างดี\n• ด้ามจับไม้ธรรมชาติ: สัมผัสนุ่มนวล จับถนัดมือสไตล์คลาสสิก\n• ขนาดกะทัดรัด: เข้าถึงซอกมุมในกระถางหรือแปลงเล็กๆ ได้แม่นยำ'},
    {'id': 9,  'name': 'ถุงมือทำสวน',            'price': '7.00',  'category': 'tools',
     'image': 'images/grow_kits/gardening_gloves.png',
     'description': '🧤 ถุงมือทำสวนปกป้องมือคุณ: นุ่มสบาย ทนทาน\n• วัสดุหนานุ่มพิเศษ: ปกป้องมือจากหนาม คมไม้ และสิ่งสกปรก\n• ดีไซน์ทูโทนสุดชิค: โทนสีน้ำตาล-เขียว สวยงามเข้าชุดกับอุปกรณ์อื่น\n• ระบายอากาศได้ดี: ไม่อับชื้น สวมใส่สบายตลอดการใช้งาน'},
    # ── เมล็ดพันธุ์ (seeds) ─────────────────────────────────────────────────
    {'id': 10, 'name': 'เมล็ดมะเขือเทศ',         'price': '1.10',  'category': 'seeds',
     'image': 'images/seeds/tomato_seeds.png',
     'description': '🍅 เมล็ดพันธุ์มะเขือเทศ\n• อัตราการงอกสูง แข็งแรงทนทาน\n• ให้ผลผลิตดก รสชาติหวานฉ่ำ\n• คัดสรรเมล็ดพันธุ์คุณภาพเพื่อการเกษตร'},
    {'id': 11, 'name': 'เมล็ดลาเวนเดอร์',         'price': '1.36',  'category': 'seeds',
     'image': 'images/seeds/lavender_seeds.png',
     'description': '💜 เมล็ดพันธุ์ลาเวนเดอร์\n• กลิ่นหอมผ่อนคลาย ช่วยสร้างบรรยากาศในสวน\n• พันธุ์พิเศษ ปลูกได้ดีในกระถางและแปลงดิน\n• ดอกสีม่วงสวยงามตลอดทั้งฤดูกาล'},
    {'id': 12, 'name': 'เมล็ดดอกไม้ป่า',          'price': '1.25',  'category': 'seeds',
     'image': 'images/seeds/wildflower_seeds.png',
     'description': '🌼 ชุดรวมเมล็ดดอกไม้ป่า\n• รวมสายพันธุ์ดอกไม้สีสันสดใสหลากชนิด\n• ช่วยสร้างระบบนิเวศที่ดีและดึงดูดแมลงที่มีประโยชน์\n• ปลูกง่าย เติบโตไว ทนทานต่อสภาพอากาศ'},
    {'id': 13, 'name': 'เมล็ดโหระพาหวาน',         'price': '0.99',  'category': 'seeds',
     'image': 'images/seeds/sweet_basil_seeds.png',
     'description': '🌿 เมล็ดพันธุ์โหระพาหวาน\n• กลิ่นหอมเป็นเอกลักษณ์ ใบใหญ่เขียวสด\n• เจริญเติบโตได้รวดเร็ว เก็บเกี่ยวได้นาน\n• เหมาะสำหรับปลูกไว้ปรุงอาหารในครัวเรือน'},
    {'id': 14, 'name': 'เมล็ดสตรอว์เบอร์รี่',     'price': '1.64',  'category': 'seeds',
     'image': 'images/seeds/strawberry_seeds.png',
     'description': '🍓 เมล็ดพันธุ์สตรอว์เบอร์รี่\n• สายพันธุ์หวานหอม คัดเกรดพรีเมียม\n• เหมาะสำหรับปลูกในกระถางแขวนหรือพื้นที่จำกัด\n• ให้ผลผลิตขนาดพอเหมาะ สีแดงสวยน่ารับประทาน'},
    {'id': 15, 'name': 'เมล็ดผักกาดหอมกูร์เมต์',  'price': '1.10',  'category': 'seeds',
     'image': 'images/seeds/gourmet_lettuce_seeds.png',
     'description': '🥬 เมล็ดผักกาดหอมกูร์เมต์\n• ใบกรอบ อร่อย ไม่มีรสขม\n• ปลูกง่ายในพื้นที่ร่มรำไร หรือปลูกแบบไฮโดรโปนิกส์\n• อุดมด้วยวิตามินและสารอาหาร'},
    {'id': 16, 'name': 'เมล็ดทานตะวัน',           'price': '0.99',  'category': 'seeds',
     'image': 'images/seeds/sunflower_seeds.png',
     'description': '🌻 เมล็ดพันธุ์ทานตะวัน\n• ดอกใหญ่ สีเหลืองสดใส แข็งแรงทนทาน\n• ปลูกเป็นไม้ประดับหรือเพื่อเก็บเกี่ยวเมล็ด\n• เจริญเติบโตไว ชอบแสงแดดจัด'},
    {'id': 17, 'name': 'เมล็ดแครอท',              'price': '0.99',  'category': 'seeds',
     'image': 'images/seeds/carrot_seeds.png',
     'description': '🥕 เมล็ดพันธุ์แครอท\n• สายพันธุ์กรอบหวาน ทรงสวย ผิวเรียบ\n• เจริญเติบโตได้ดีในดินร่วนซุย\n• ปลอดสารเคมี ปลอดภัยต่อการบริโภค'},
    {'id': 18, 'name': 'เมล็ดมะเขือยาว',          'price': '1.64',  'category': 'seeds',
     'image': 'images/seeds/eggplant_seeds.png',
     'description': '🍆 เมล็ดพันธุ์มะเขือยาว\n• ผลยาวทรงสวย เนื้อนุ่ม รสชาติดี\n• ทนทานต่อโรคและแมลงได้ดี\n• ให้ผลผลิตต่อเนื่องยาวนาน'},
    {'id': 19, 'name': 'เมล็ดพริก',               'price': '0.99',  'category': 'seeds',
     'image': 'images/seeds/chili_pepper_seeds.png',
     'description': '🌶️ เมล็ดพันธุ์พริกคัดพิเศษ\n• รสชาติเผ็ดร้อน สดชื่น ผลดก\n• ปลูกง่ายในกระถางหรือริมรั้ว\n• ทนทานต่อสภาพอากาศร้อนได้ดีเยี่ยม'},
    {'id': 20, 'name': 'เมล็ดแตงกวา',             'price': '1.50',  'category': 'seeds',
     'image': 'images/seeds/cucumber_seeds.png',
     'description': '🥒 เมล็ดพันธุ์แตงกวา\n• ผลกรอบฉ่ำน้ำ ไร้กลิ่นเหม็นเขียว\n• สายพันธุ์เลื้อยไว ให้ผลผลิตเร็ว\n• เหมาะสำหรับปลูกเป็นผักสวนครัว'},
    {'id': 21, 'name': 'เมล็ดฟักทอง',             'price': '1.99',  'category': 'seeds',
     'image': 'images/seeds/pumpkin_seeds.png',
     'description': '🎃 เมล็ดพันธุ์ฟักทอง\n• เนื้อเหนียวนุ่ม รสชาติหวานมัน\n• ผลขนาดใหญ่ แข็งแรง เก็บรักษาได้นาน\n• อัตราการงอกสูง ดูแลง่าย'},
    # ── ผลิตภัณฑ์ธรรมชาติ — น้ำมันหอมระเหย (natural) ──────────────────────
    {'id': 22, 'name': 'น้ำมันหอมระเหยเปปเปอร์มินต์', 'price': '6.00', 'category': 'natural',
     'image': 'images/natural_products/peppermint_essential_oil.png',
     'description': '🌿 น้ำมันหอมระเหยเปปเปอร์มินต์ (Peppermint)\n• กลิ่นหอมเย็นสดชื่น ช่วยให้รู้สึกตื่นตัวและมีสมาธิ\n• บรรเทาอาการคัดจมูกและช่วยให้ระบบทางเดินหายใจโล่ง\n• สกัดจากธรรมชาติ 100% ปลอดภัยต่อการใช้งาน'},
    {'id': 23, 'name': 'น้ำมันหอมระเหยคาโมมายล์',    'price': '6.00', 'category': 'natural',
     'image': 'images/natural_products/chamomile_essential_oil.png',
     'description': '🌼 น้ำมันหอมระเหยคาโมมายล์ (Chamomile)\n• กลิ่นหอมอ่อนโยน ช่วยให้รู้สึกผ่อนคลายและลดความเครียด\n• เหมาะสำหรับใช้ก่อนนอนเพื่อช่วยให้หลับสบายยิ่งขึ้น\n• ปลอดภัยและอ่อนโยนต่อผิวพรรณ'},
    {'id': 24, 'name': 'น้ำมันหอมระเหยกุหลาบ',        'price': '6.00', 'category': 'natural',
     'image': 'images/natural_products/rose_essential_oil.png',
     'description': '🌹 น้ำมันหอมระเหยกุหลาบ (Rose)\n• กลิ่นหอมหรูหรา ช่วยปรับสมดุลอารมณ์และสร้างความโรแมนติก\n• มีคุณสมบัติในการบำรุงผิวให้ดูสุขภาพดีและอ่อนเยาว์\n• สกัดเข้มข้นจากกลีบกุหลาบสายพันธุ์ดี'},
    {'id': 25, 'name': 'น้ำมันหอมระเหยหญ้าแฝก',       'price': '6.00', 'category': 'natural',
     'image': 'images/natural_products/vetiver_essential_oil.png',
     'description': '🌾 น้ำมันหอมระเหยหญ้าแฝก (Vetiver)\n• กลิ่นหอมแนว Woody ให้ความรู้สึกสงบและมั่นคง\n• ช่วยลดอาการวิตกกังวลและทำให้จิตใจสงบนิ่ง\n• นิยมใช้ในการทำสมาธิและปรับบรรยากาศให้นิ่งลึก'},
    {'id': 26, 'name': 'น้ำมันหอมระเหยลาเวนเดอร์',    'price': '6.00', 'category': 'natural',
     'image': 'images/natural_products/lavender_essential_oil.png',
     'description': '💜 น้ำมันหอมระเหยลาเวนเดอร์ (Lavender)\n• กลิ่นยอดนิยมที่ช่วยสร้างความผ่อนคลายในทุกช่วงเวลา\n• ช่วยบรรเทาอาการปวดศีรษะและช่วยให้นอนหลับง่ายขึ้น\n• อเนกประสงค์ ใช้งานได้ทั้งในเครื่องพ่นหรือผสมน้ำมันนวด'},
    {'id': 27, 'name': 'น้ำมันหอมระเหยไม้จันทน์หอม',  'price': '6.00', 'category': 'natural',
     'image': 'images/natural_products/sandalwood_essential_oil.png',
     'description': '🪵 น้ำมันหอมระเหยไม้จันทน์หอม (Sandalwood)\n• กลิ่นหอมอบอุ่นและมีเสน่ห์แบบคลาสสิก\n• ช่วยเพิ่มสมาธิและปรับสภาพจิตใจให้ผ่องใส\n• มีคุณสมบัติช่วยปลอบประโลมผิวอย่างอ่อนโยน'},
    {'id': 28, 'name': 'น้ำมันหอมระเหยตะไคร้หอม',     'price': '6.00', 'category': 'natural',
     'image': 'images/natural_products/citronella_essential_oil.png',
     'description': '🌱 น้ำมันหอมระเหยตะไคร้หอม (Citronella)\n• กลิ่นหอมสะอาด สดชื่น ช่วยไล่แมลงได้อย่างเป็นธรรมชาติ\n• ช่วยลดความเหนื่อยล้าและให้ความรู้สึกกระปรี้กระเปร่า\n• เหมาะสำหรับใช้ปรับอากาศในบ้านหรือในสวน'},
    {'id': 29, 'name': 'น้ำมันหอมระเหยส้มหวาน',        'price': '6.00', 'category': 'natural',
     'image': 'images/natural_products/sweet_orange_essential_oil.png',
     'description': '🍊 น้ำมันหอมระเหยส้มหวาน (Sweet Orange)\n• กลิ่นหอมสดใส ช่วยเติมพลังงานและลดอาการหดหู่\n• ปรับบรรยากาศให้ดูอบอุ่นและเป็นกันเอง\n• สกัดจากผิวส้มสด ให้ความรู้สึกเป็นธรรมชาติอย่างแท้จริง'},
    # ── อโรมาเธอราพี (aroma) ────────────────────────────────────────────────
    {'id': 30, 'name': 'เครื่องอโรมาทรงกรวย (เขียวมะกอก)', 'price': '24.00', 'category': 'aroma',
     'image': 'images/aroma/aroma_diffuser_1.png',
     'description': '🌿 เครื่องพ่นอโรมาดีไซน์มินิมอล\n• ดีไซน์ทรงกรวยสีเขียวมะกอก ตัดกับฐานลายไม้ธรรมชาติสวยงาม\n• ระบบพ่นละอองไอน้ำแบบละเอียด กระจายกลิ่นหอมได้ทั่วถึง\n• มีไฟ LED แสดงสถานะการทำงานและช่วยสร้างบรรยากาศผ่อนคลาย'},
    {'id': 31, 'name': 'เครื่องอโรมาทรงสูง (เทาดำ)',        'price': '18.99', 'category': 'aroma',
     'image': 'images/aroma/aroma_diffuser_2.png',
     'description': '🏙️ เครื่องพ่นอโรมาทรงโมเดิร์น\n• รูปทรงเพรียวสูงประหยัดพื้นที่ เหมาะสำหรับวางบนโต๊ะทำงาน\n• ตัวเครื่องสีเทาดำสไตล์เท่ ตัดกับฐานไม้ดูทันสมัย\n• ระบบทำงานเงียบสนิท ไม่รบกวนเวลาพักผ่อนหรือการทำงาน'},
    {'id': 32, 'name': 'เครื่องอโรมาทรงกระบอก (ดำขาว)',     'price': '20.00', 'category': 'aroma',
     'image': 'images/aroma/aroma_diffuser_3.png',
     'description': '🖤 เครื่องพ่นอโรมาสไตล์ทูโทน\n• ดีไซน์ทรงกระบอกเรียบหรูสีดำตัดขาว\n• ฐานลายไม้ช่วยเพิ่มความรู้สึกอบอุ่นเป็นธรรมชาติ\n• ตัวเครื่องทำจากวัสดุคุณภาพดี ทนทานต่อการใช้งานยาวนาน'},
    {'id': 33, 'name': 'เครื่องอโรมาทรงลูกบาศก์ (ขาวนวล)',  'price': '15.99', 'category': 'aroma',
     'image': 'images/aroma/aroma_diffuser_4.png',
     'description': '🤍 เครื่องพ่นอโรมาดีไซน์โค้งมน\n• รูปทรงลูกบาศก์สีขาวสะอาดตา ให้ความรู้สึกละมุนละไม\n• ช่องพ่นไอน้ำกว้างพิเศษ กระจายความหอมได้รวดเร็ว\n• ขนาดกะทัดรัด เคลื่อนย้ายไปตามมุมต่าง ๆ ของบ้านได้ง่าย'},
    {'id': 34, 'name': 'เครื่องอโรมาทรงกระบอก (ขาวไม้)',    'price': '15.99', 'category': 'aroma',
     'image': 'images/aroma/aroma_diffuser_5.png',
     'description': '✨ เครื่องพ่นอโรมาแนวมินิมอล-เซน\n• ตัวเครื่องสีขาวเนียนตาตัดกับส่วนล่างที่เป็นลายไม้สว่าง\n• ดีไซน์เรียบง่ายแต่ดูดี เข้าได้กับทุกสไตล์การตกแต่งห้อง\n• มีปุ่มควบคุมที่ใช้งานง่าย ไม่ยุ่งยากซับซ้อน'},
    {'id': 35, 'name': 'เครื่องอโรมาทรงสี่เหลี่ยม (กรมท่า)', 'price': '20.00', 'category': 'aroma',
     'image': 'images/aroma/aroma_diffuser_6.png',
     'description': '💙 เครื่องพ่นอโรมาสีสุขุมพรีเมียม\n• ตัวเครื่องสีน้ำเงินกรมท่าตัดฐานไม้ ให้ลุคพรีเมียมและสุขุม\n• เหมาะสำหรับใช้ในห้องนอนหรือห้องรับแขกเพื่อสร้างบรรยากาศ\n• ระบบตัดไฟอัตโนมัติเมื่อน้ำหมด เพื่อความปลอดภัยสูงสุด'},
    # ── ผลิตภัณฑ์ธรรมชาติ — ดอกไม้แห้ง (natural) ───────────────────────────
    {'id': 36, 'name': 'ดอกสแตติสแห้ง',           'price': '5.00', 'category': 'natural',
     'image': 'images/natural_products/statice.png',
     'description': '💐 ดอกสแตติสแห้ง (Statice)\n• สัญลักษณ์แห่งความรู้สึกดีๆ ที่คงอยู่ตลอดไป\n• สีสันสดใสยาวนาน ไม่ร่วงโรยง่ายแม้เป็นดอกไม้แห้ง\n• เหมาะสำหรับจัดช่อดอกไม้ ของขวัญ หรือตกแต่งบ้านสไตล์วินเทจ'},
    {'id': 37, 'name': 'ดอกยิปโซฟิลลาแห้ง',        'price': '5.00', 'category': 'natural',
     'image': 'images/natural_products/gypsophila.png',
     'description': '☁️ ดอกยิปโซฟิลลา (Gypsophila)\n• ดอกไม้สีขาวนวลขนาดเล็ก ให้ความรู้สึกอ่อนโยนและบริสุทธิ์\n• คงรูปทรงสวยงามได้นาน ช่วยเพิ่มเลเยอร์ให้กับแจกันดอกไม้\n• ตกแต่งมุมห้องให้ดูละมุนตาและมีชีวิตชีวา'},
    {'id': 38, 'name': 'ดอกสตอร์วฟลาวเวอร์แห้ง',   'price': '5.00', 'category': 'natural',
     'image': 'images/natural_products/strawflower.png',
     'description': '☀️ ดอกสตอร์วฟลาวเวอร์ (Strawflower)\n• กลีบดอกมีลักษณะพิเศษที่ให้สัมผัสเหมือนกระดาษและคงทนสูง\n• โทนสีเหลืองส้มสดใส ช่วยเติมพลังงานบวกให้กับพื้นที่\n• นิยมใช้ประดับในงานฝีมือและงาน DIY ต่างๆ'},
    {'id': 39, 'name': 'ลาเวนเดอร์แห้ง',            'price': '5.00', 'category': 'natural',
     'image': 'images/natural_products/dried_lavender.png',
     'description': '💜 ลาเวนเดอร์แห้ง (Lavender)\n• กลิ่นหอมสะอาดที่เป็นเอกลักษณ์ ช่วยให้รู้สึกผ่อนคลาย\n• มอบบรรยากาศสไตล์ทุ่งดอกไม้ในยุโรปให้กับบ้านคุณ\n• สามารถวางไว้ในห้องนอนเพื่อช่วยให้การพักผ่อนดีขึ้น'},
    {'id': 40, 'name': 'กุหลาบแห้ง',               'price': '5.00', 'category': 'flowers',
     'image': 'images/natural_products/dried_rose.png',
     'description': '🌹 ดอกกุหลาบแห้ง (Dried Rose)\n• คัดสรรดอกกุหลาบสีแดงเข้มทรงสวย นำมาผ่านกระบวนการอบแห้งอย่างประณีต\n• เก็บรักษาความคลาสสิกและเสน่ห์ของกุหลาบไว้ได้ยาวนาน\n• สื่อถึงความรักที่เป็นอมตะ เหมาะสำหรับโอกาสพิเศษ'},
    {'id': 41, 'name': 'ไฮเดรนเยียแห้ง',            'price': '5.00', 'category': 'natural',
     'image': 'images/natural_products/dried_hydrangea.png',
     'description': '🌸 ดอกไฮเดรนเยียแห้ง (Hydrangea)\n• ช่อดอกขนาดใหญ่ที่มีเอกลักษณ์เฉพาะตัว\n• โทนสีตุ่นสวยงาม เหมาะกับการตกแต่งสไตล์คาเฟ่หรือโฮมมี่\n• ช่วยสร้างจุดดึงดูดสายตาให้กับแจกันใบโปรดของคุณ'},
    {'id': 42, 'name': 'โรสแมรี่แห้ง',              'price': '5.00', 'category': 'natural',
     'image': 'images/natural_products/dried_rosemary.png',
     'description': '🌿 โรสแมรี่แห้ง (Dried Rosemary)\n• กลิ่นหอมสมุนไพรที่ช่วยให้รู้สึกสดชื่นและปลอดโปร่ง\n• นอกจากความสวยงามยังให้กลิ่นอายธรรมชาติที่ผ่อนคลาย\n• ประดับตกแต่งช่อดอกไม้หรือวางในครัวเพื่อความสวยงาม'},
]


class Command(BaseCommand):
    help = 'Seed 42 products into DB, preserving original IDs. Safe to re-run.'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for data in PRODUCTS:
            pid = data['id']
            defaults = {
                'name':           data['name'],
                'slug':           f'product-{pid}',
                'price':          Decimal(data['price']),
                'image':          data['image'],
                'description':    data['description'],
                'category':       data['category'],
                'stock_quantity': 50,
                'is_active':      True,
            }
            obj, created = Product.objects.update_or_create(pk=pid, defaults=defaults)
            if created:
                created_count += 1
                self.stdout.write(f'  CREATED id={pid}: {data["name"]}')
            else:
                updated_count += 1
                self.stdout.write(f'  UPDATED id={pid}: {data["name"]}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone: {created_count} created, {updated_count} updated '
            f'({created_count + updated_count} total)'
        ))

        # Report any ID gaps that might cause issues
        db_ids = set(Product.objects.values_list('id', flat=True))
        expected = set(range(1, 43))
        missing = expected - db_ids
        if missing:
            self.stdout.write(self.style.WARNING(f'Missing IDs: {sorted(missing)}'))
        else:
            self.stdout.write(self.style.SUCCESS('All IDs 1-42 present in DB ✓'))
