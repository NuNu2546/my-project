from django.shortcuts import render, redirect
from django.http import Http404
from datetime import datetime, timedelta

ALL_PRODUCTS = [
    {
        'id': 1,
        'name': 'บัวรดน้ำ',
        'price': 6.00,
        'description': '''🚿 บัวรดน้ำคุณภาพสูง
• ดีไซน์จับถนัดมือ รดน้ำได้แม่นยำ
• วัสดุทนทาน ทนแดดทนฝน
• อัตราการไหลของน้ำสม่ำเสมอ เหมาะสำหรับพืชทุกชนิด''',
        'image': 'images/grow_kits/watering_can.png',
        'category': 'tools'
    },
    {
        'id': 2,
        'name': 'ถุงขยะสวน',
        'price': 6.00,
        'description': '''🗑️ ถุงขยะสวนเอนกประสงค์
• จุของได้เยอะ เหมาะสำหรับเศษใบไม้และกิ่งไม้
• วัสดุเหนียวพิเศษ ไม่ขาดง่าย
• พับเก็บได้ ประหยัดพื้นที่ และทำความสะอาดง่าย''',
        'image': 'images/grow_kits/garden_waste_bags.png',
        'category': 'tools'
    },
    {
        'id': 3,
        'name': 'ป้ายชื่อต้นไม้',
        'price': 2.00,
        'description': '''🏷️ ป้ายชื่อต้นไม้
• ช่วยจัดระเบียบสวนให้ดูเป็นมืออาชีพ
• เขียนง่าย ติดทนนาน ไม่หลุดลอกง่าย
• ทนต่อความชื้นและแสงแดด''',
        'image': 'images/grow_kits/plant_labels.png',
        'category': 'tools'
    },
    {
        'id': 4,
        'name': 'กระถาง & ถาดเพาะเมล็ด',
        'price': 2.00,
        'description': '''🌱 ชุดเริ่มต้นความสุข: กระถาง & ถาดเพาะเมล็ด
• ดีไซน์มินิมอล: กระถางโทนสีอิฐธรรมชาติ เข้าได้กับทุกมุมในบ้าน
• ฟังก์ชันครบ: มีทั้งถาดหลุมสำหรับเพาะกล้าและกระถางหลายขนาด
• คุณภาพพรีเมียม: วัสดุแข็งแรง ระบายน้ำและอากาศได้ดี ช่วยให้รากเดินสะดวก''',
        'image': 'images/grow_kits/pots_and_seed_trays.png',
        'category': 'tools'
    },
    {
        'id': 5,
        'name': 'สายยางพร้อมหัวฉีด',
        'price': 12.00,
        'description': '''🚿 สายยางพร้อมหัวฉีดดีไซน์พรีเมียม
• หัวฉีดละอองละเอียด: ถนอมต้นกล้าและหน้าดิน ไม่ให้กระจายตัวแรง
• สายยางคุณภาพสูง: ยืดหยุ่นได้ดี ไม่พันกัน และทนทานต่อแรงดันน้ำ
• ด้ามจับลายไม้: สวยงามคลาสสิก และช่วยให้จับกระชับมือยิ่งขึ้น''',
        'image': 'images/grow_kits/hose_with_spray_nozzle.png',
        'category': 'tools'
    },
    {
        'id': 6,
        'name': 'กรรไกรตัดกิ่งยาว',
        'price': 20.00,
        'description': '''✂️ กรรไกรตัดกิ่งพรีเมียม: คมกริบ ผ่อนแรง
• ใบมีดเหล็กคุณภาพสูง: ตัดกิ่งได้เรียบเนียน ไม่ทำให้เนื้อไม้ช้ำ
• ระบบสปริงนุ่มนวล: ช่วยผ่อนแรงในทุกการตัด ลดความเมื่อยล้า
• ด้ามจับลายไม้: ดีไซน์สวยงามตามหลักสรีรศาสตร์ จับถนัดมือ''',
        'image': 'images/grow_kits/long_handle_pruning_shears.png',
        'category': 'tools'
    },
    {
        'id': 7,
        'name': 'พลั่ว',
        'price': 20.00,
        'description': '''⛏️ พลั่วตักดินพรีเมียม: แข็งแกร่ง ทนทาน
• วัสดุสเตนเลส: ผิวมันเงา ไม่เป็นสนิมง่าย แข็งแรงทนทาน
• ด้ามจับตัว Y: ออกแบบให้รับกับแรงกด ช่วยให้ขุดหรือตักดินได้ง่าย
• เอนกประสงค์: เหมาะทั้งการขุดหลุมปลูก ย้ายต้นกล้า หรือผสมดิน''',
        'image': 'images/grow_kits/garden_shovel.png',
        'category': 'tools'
    },
    {
        'id': 8,
        'name': 'คราด',
        'price': 20.00,
        'description': '''🍂 คราดพรวนดินพรีเมียม: เตรียมหน้าดินให้พร้อม
• ซี่คราดเหล็กกล้า: ตะกุยดินที่จับตัวเป็นก้อนให้ร่วนซุยได้อย่างดี
• ด้ามจับไม้ธรรมชาติ: สัมผัสนุ่มนวล จับถนัดมือสไตล์คลาสสิก
• ขนาดกะทัดรัด: เข้าถึงซอกมุมในกระถางหรือแปลงเล็กๆ ได้แม่นยำ''',
        'image': 'images/grow_kits/garden_rake.png',
        'category': 'tools'
    },
    {
        'id': 9,
        'name': 'ถุงมือทำสวน',
        'price': 7.00,
        'description': '''🧤 ถุงมือทำสวนปกป้องมือคุณ: นุ่มสบาย ทนทาน
• วัสดุหนานุ่มพิเศษ: ปกป้องมือจากหนาม คมไม้ และสิ่งสกปรก
• ดีไซน์ทูโทนสุดชิค: โทนสีน้ำตาล-เขียว สวยงามเข้าชุดกับอุปกรณ์อื่น
• ระบายอากาศได้ดี: ไม่อับชื้น สวมใส่สบายตลอดการใช้งาน''',
        'image': 'images/grow_kits/gardening_gloves.png',
        'category': 'tools'
    },
    # --- หมวดหมู่ เมล็ดพันธุ์ (Seeds) ---
    {
        'id': 10,
        'name': 'เมล็ดมะเขือเทศ',
        'price': 1.10,
        'description': '''🍅 เมล็ดพันธุ์มะเขือเทศ
• อัตราการงอกสูง แข็งแรงทนทาน
• ให้ผลผลิตดก รสชาติหวานฉ่ำ
• คัดสรรเมล็ดพันธุ์คุณภาพเพื่อการเกษตร''',
        'image': 'images/seeds/tomato_seeds.png',
        'category': 'seeds'
    },
    {
        'id': 11,
        'name': 'เมล็ดลาเวนเดอร์',
        'price': 1.36,
        'description': '''💜 เมล็ดพันธุ์ลาเวนเดอร์
• กลิ่นหอมผ่อนคลาย ช่วยสร้างบรรยากาศในสวน
• พันธุ์พิเศษ ปลูกได้ดีในกระถางและแปลงดิน
• ดอกสีม่วงสวยงามตลอดทั้งฤดูกาล''',
        'image': 'images/seeds/lavender_seeds.png',
        'category': 'seeds'
    },
    {
        'id': 12,
        'name': 'เมล็ดดอกไม้ป่า',
        'price': 1.25,
        'description': '''🌼 ชุดรวมเมล็ดดอกไม้ป่า
• รวมสายพันธุ์ดอกไม้สีสันสดใสหลากชนิด
• ช่วยสร้างระบบนิเวศที่ดีและดึงดูดแมลงที่มีประโยชน์
• ปลูกง่าย เติบโตไว ทนทานต่อสภาพอากาศ''',
        'image': 'images/seeds/wildflower_seeds.png',
        'category': 'seeds'
    },
    {
        'id': 13,
        'name': 'เมล็ดโหระพาหวาน',
        'price': 0.99,
        'description': '''🌿 เมล็ดพันธุ์โหระพาหวาน
• กลิ่นหอมเป็นเอกลักษณ์ ใบใหญ่เขียวสด
• เจริญเติบโตได้รวดเร็ว เก็บเกี่ยวได้นาน
• เหมาะสำหรับปลูกไว้ปรุงอาหารในครัวเรือน''',
        'image': 'images/seeds/sweet_basil_seeds.png',
        'category': 'seeds'
    },
    {
        'id': 14,
        'name': 'เมล็ดสตรอว์เบอร์รี่',
        'price': 1.64,
        'description': '''🍓 เมล็ดพันธุ์สตรอว์เบอร์รี่
• สายพันธุ์หวานหอม คัดเกรดพรีเมียม
• เหมาะสำหรับปลูกในกระถางแขวนหรือพื้นที่จำกัด
• ให้ผลผลิตขนาดพอเหมาะ สีแดงสวยน่ารับประทาน''',
        'image': 'images/seeds/strawberry_seeds.png',
        'category': 'seeds'
    },
    {
        'id': 15,
        'name': 'เมล็ดผักกาดหอมกูร์เมต์',
        'price': 1.10,
        'description': '''🥬 เมล็ดผักกาดหอมกูร์เมต์
• ใบกรอบ อร่อย ไม่มีรสขม
• ปลูกง่ายในพื้นที่ร่มรำไร หรือปลูกแบบไฮโดรโปนิกส์
• อุดมด้วยวิตามินและสารอาหาร''',
        'image': 'images/seeds/gourmet_lettuce_seeds.png',
        'category': 'seeds'
    },
    {
        'id': 16,
        'name': 'เมล็ดทานตะวัน',
        'price': 0.99,
        'description': '''🌻 เมล็ดพันธุ์ทานตะวัน
• ดอกใหญ่ สีเหลืองสดใส แข็งแรงทนทาน
• ปลูกเป็นไม้ประดับหรือเพื่อเก็บเกี่ยวเมล็ด
• เจริญเติบโตไว ชอบแสงแดดจัด''',
        'image': 'images/seeds/sunflower_seeds.png',
        'category': 'seeds'
    },
    {
        'id': 17,
        'name': 'เมล็ดแครอท',
        'price': 0.99,
        'description': '''🥕 เมล็ดพันธุ์แครอท
• สายพันธุ์กรอบหวาน ทรงสวย ผิวเรียบ
• เจริญเติบโตได้ดีในดินร่วนซุย
• ปลอดสารเคมี ปลอดภัยต่อการบริโภค''',
        'image': 'images/seeds/carrot_seeds.png',
        'category': 'seeds'
    },
    {
        'id': 18,
        'name': 'เมล็ดมะเขือยาว',
        'price': 1.64,
        'description': '''🍆 เมล็ดพันธุ์มะเขือยาว
• ผลยาวทรงสวย เนื้อนุ่ม รสชาติดี
• ทนทานต่อโรคและแมลงได้ดี
• ให้ผลผลิตต่อเนื่องยาวนาน''',
        'image': 'images/seeds/eggplant_seeds.png',
        'category': 'seeds'
    },
    {
        'id': 19,
        'name': 'เมล็ดพริก',
        'price': 0.99,
        'description': '''🌶️ เมล็ดพันธุ์พริกคัดพิเศษ
• รสชาติเผ็ดร้อน สดชื่น ผลดก
• ปลูกง่ายในกระถางหรือริมรั้ว
• ทนทานต่อสภาพอากาศร้อนได้ดีเยี่ยม''',
        'image': 'images/seeds/chili_pepper_seeds.png',
        'category': 'seeds'
    },
    {
        'id': 20,
        'name': 'เมล็ดแตงกวา',
        'price': 1.50,
        'description': '''🥒 เมล็ดพันธุ์แตงกวา
• ผลกรอบฉ่ำน้ำ ไร้กลิ่นเหม็นเขียว
• สายพันธุ์เลื้อยไว ให้ผลผลิตเร็ว
• เหมาะสำหรับปลูกเป็นผักสวนครัว''',
        'image': 'images/seeds/cucumber_seeds.png',
        'category': 'seeds'
    },
    {
        'id': 21,
        'name': 'เมล็ดฟักทอง',
        'price': 1.99,
        'description': '''🎃 เมล็ดพันธุ์ฟักทอง
• เนื้อเหนียวนุ่ม รสชาติหวานมัน
• ผลขนาดใหญ่ แข็งแรง เก็บรักษาได้นาน
• อัตราการงอกสูง ดูแลง่าย''',
        'image': 'images/seeds/pumpkin_seeds.png',
        'category': 'seeds'
    },
    {
        'id': 22,
        'name': 'น้ำมันหอมระเหยเปปเปอร์มินต์',
        'price': 6.00,
        'description': '''🌿 น้ำมันหอมระเหยเปปเปอร์มินต์ (Peppermint)
• กลิ่นหอมเย็นสดชื่น ช่วยให้รู้สึกตื่นตัวและมีสมาธิ
• บรรเทาอาการคัดจมูกและช่วยให้ระบบทางเดินหายใจโล่ง
• สกัดจากธรรมชาติ 100% ปลอดภัยต่อการใช้งาน''',
        'image': 'images/natural_products/peppermint_essential_oil.png',
        'category': 'natural'
    },
    {
        'id': 23,
        'name': 'น้ำมันหอมระเหยคาโมมายล์',
        'price': 6.00,
        'description': '''🌼 น้ำมันหอมระเหยคาโมมายล์ (Chamomile)
• กลิ่นหอมอ่อนโยน ช่วยให้รู้สึกผ่อนคลายและลดความเครียด
• เหมาะสำหรับใช้ก่อนนอนเพื่อช่วยให้หลับสบายยิ่งขึ้น
• ปลอดภัยและอ่อนโยนต่อผิวพรรณ''',
        'image': 'images/natural_products/chamomile_essential_oil.png',
        'category': 'natural'
    },
    {
        'id': 24,
        'name': 'น้ำมันหอมระเหยกุหลาบ',
        'price': 6.00,
        'description': '''🌹 น้ำมันหอมระเหยกุหลาบ (Rose)
• กลิ่นหอมหรูหรา ช่วยปรับสมดุลอารมณ์และสร้างความโรแมนติก
• มีคุณสมบัติในการบำรุงผิวให้ดูสุขภาพดีและอ่อนเยาว์
• สกัดเข้มข้นจากกลีบกุหลาบสายพันธุ์ดี''',
        'image': 'images/natural_products/rose_essential_oil.png',
        'category': 'natural'
    },
    {
        'id': 25,
        'name': 'น้ำมันหอมระเหยหญ้าแฝก',
        'price': 6.00,
        'description': '''🌾 น้ำมันหอมระเหยหญ้าแฝก (Vetiver)
• กลิ่นหอมแนว Woody ให้ความรู้สึกสงบและมั่นคง
• ช่วยลดอาการวิตกกังวลและทำให้จิตใจสงบนิ่ง
• นิยมใช้ในการทำสมาธิและปรับบรรยากาศให้นิ่งลึก''',
        'image': 'images/natural_products/vetiver_essential_oil.png',
        'category': 'natural'
    },
    {
        'id': 26,
        'name': 'น้ำมันหอมระเหยลาเวนเดอร์',
        'price': 6.00,
        'description': '''💜 น้ำมันหอมระเหยลาเวนเดอร์ (Lavender)
• กลิ่นยอดนิยมที่ช่วยสร้างความผ่อนคลายในทุกช่วงเวลา
• ช่วยบรรเทาอาการปวดศีรษะและช่วยให้นอนหลับง่ายขึ้น
• อเนกประสงค์ ใช้งานได้ทั้งในเครื่องพ่นหรือผสมน้ำมันนวด''',
        'image': 'images/natural_products/lavender_essential_oil.png',
        'category': 'natural'
    },
    {
        'id': 27,
        'name': 'น้ำมันหอมระเหยไม้จันทน์หอม',
        'price': 6.00,
        'description': '''🪵 น้ำมันหอมระเหยไม้จันทน์หอม (Sandalwood)
• กลิ่นหอมอบอุ่นและมีเสน่ห์แบบคลาสสิก
• ช่วยเพิ่มสมาธิและปรับสภาพจิตใจให้ผ่องใส
• มีคุณสมบัติช่วยปลอบประโลมผิวอย่างอ่อนโยน''',
        'image': 'images/natural_products/sandalwood_essential_oil.png',
        'category': 'natural'
    },
    {
        'id': 28,
        'name': 'น้ำมันหอมระเหยตะไคร้หอม',
        'price': 6.00,
        'description': '''🌱 น้ำมันหอมระเหยตะไคร้หอม (Citronella)
• กลิ่นหอมสะอาด สดชื่น ช่วยไล่แมลงได้อย่างเป็นธรรมชาติ
• ช่วยลดความเหนื่อยล้าและให้ความรู้สึกกระปรี้กระเปร่า
• เหมาะสำหรับใช้ปรับอากาศในบ้านหรือในสวน''',
        'image': 'images/natural_products/citronella_essential_oil.png',
        'category': 'natural'
    },
    {
        'id': 29,
        'name': 'น้ำมันหอมระเหยส้มหวาน',
        'price': 6.00,
        'description': '''🍊 น้ำมันหอมระเหยส้มหวาน (Sweet Orange)
• กลิ่นหอมสดใส ช่วยเติมพลังงานและลดอาการหดหู่
• ปรับบรรยากาศให้ดูอบอุ่นและเป็นกันเอง
• สกัดจากผิวส้มสด ให้ความรู้สึกเป็นธรรมชาติอย่างแท้จริง''',
        'image': 'images/natural_products/sweet_orange_essential_oil.png',
        'category': 'natural'
    },
    
    {
        'id': 30,
        'name': 'เครื่องอโรมาทรงกรวย (เขียวมะกอก)',
        'price': 24.00,
        'description': '''🌿 เครื่องพ่นอโรมาดีไซน์มินิมอล
• ดีไซน์ทรงกรวยสีเขียวมะกอก ตัดกับฐานลายไม้ธรรมชาติสวยงาม
• ระบบพ่นละอองไอน้ำแบบละเอียด กระจายกลิ่นหอมได้ทั่วถึง
• มีไฟ LED แสดงสถานะการทำงานและช่วยสร้างบรรยากาศผ่อนคลาย''',
        'image': 'images/aroma/aroma_diffuser_1.png',
        'category': 'aroma'
    },
    {
        'id': 31,
        'name': 'เครื่องอโรมาทรงสูง (เทาดำ)',
        'price': 18.99,
        'description': '''🏙️ เครื่องพ่นอโรมาทรงโมเดิร์น
• รูปทรงเพรียวสูงประหยัดพื้นที่ เหมาะสำหรับวางบนโต๊ะทำงาน
• ตัวเครื่องสีเทาดำสไตล์เท่ ตัดกับฐานไม้ดูทันสมัย
• ระบบทำงานเงียบสนิท ไม่รบกวนเวลาพักผ่อนหรือการทำงาน''',
        'image': 'images/aroma/aroma_diffuser_2.png',
        'category': 'aroma'
    },
    {
        'id': 32,
        'name': 'เครื่องอโรมาทรงกระบอก (ดำขาว)',
        'price': 20.00,
        'description': '''🖤 เครื่องพ่นอโรมาสไตล์ทูโทน
• ดีไซน์ทรงกระบอกเรียบหรูสีดำตัดขาว
• ฐานลายไม้ช่วยเพิ่มความรู้สึกอบอุ่นเป็นธรรมชาติ
• ตัวเครื่องทำจากวัสดุคุณภาพดี ทนทานต่อการใช้งานยาวนาน''',
        'image': 'images/aroma/aroma_diffuser_3.png',
        'category': 'aroma'
    },
    {
        'id': 33,
        'name': 'เครื่องอโรมาทรงลูกบาศก์ (ขาวนวล)',
        'price': 15.99,
        'description': '''🤍 เครื่องพ่นอโรมาดีไซน์โค้งมน
• รูปทรงลูกบาศก์สีขาวสะอาดตา ให้ความรู้สึกละมุนละไม
• ช่องพ่นไอน้ำกว้างพิเศษ กระจายความหอมได้รวดเร็ว
• ขนาดกะทัดรัด เคลื่อนย้ายไปตามมุมต่าง ๆ ของบ้านได้ง่าย''',
        'image': 'images/aroma/aroma_diffuser_4.png',
        'category': 'aroma'
    },
    {
        'id': 34,
        'name': 'เครื่องอโรมาทรงกระบอก (ขาวไม้)',
        'price': 15.99,
        'description': '''✨ เครื่องพ่นอโรมาแนวมินิมอล-เซน
• ตัวเครื่องสีขาวเนียนตาตัดกับส่วนล่างที่เป็นลายไม้สว่าง
• ดีไซน์เรียบง่ายแต่ดูดี เข้าได้กับทุกสไตล์การตกแต่งห้อง
• มีปุ่มควบคุมที่ใช้งานง่าย ไม่ยุ่งยากซับซ้อน''',
        'image': 'images/aroma/aroma_diffuser_5.png',
        'category': 'aroma'
    },
    {
        'id': 35,
        'name': 'เครื่องอโรมาทรงสี่เหลี่ยม (กรมท่า)',
        'price': 20.00,
        'description': '''💙 เครื่องพ่นอโรมาสีสุขุมพรีเมียม
• ตัวเครื่องสีน้ำเงินกรมท่าตัดฐานไม้ ให้ลุคพรีเมียมและสุขุม
• เหมาะสำหรับใช้ในห้องนอนหรือห้องรับแขกเพื่อสร้างบรรยากาศ
• ระบบตัดไฟอัตโนมัติเมื่อน้ำหมด เพื่อความปลอดภัยสูงสุด''',
        'image': 'images/aroma/aroma_diffuser_6.png',
        'category': 'aroma'
    },
    {
        'id': 36,
        'name': 'ดอกสแตติสแห้ง',
        'price': 5.00,
        'description': '''💐 ดอกสแตติสแห้ง (Statice)
• สัญลักษณ์แห่งความรู้สึกดีๆ ที่คงอยู่ตลอดไป
• สีสันสดใสยาวนาน ไม่ร่วงโรยง่ายแม้เป็นดอกไม้แห้ง
• เหมาะสำหรับจัดช่อดอกไม้ ของขวัญ หรือตกแต่งบ้านสไตล์วินเทจ''',
        'image': 'images/natural_products/statice.png',
        'category': 'natural'
    },
    {
        'id': 37,
        'name': 'ดอกยิปโซฟิลลาแห้ง',
        'price': 5.00,
        'description': '''☁️ ดอกยิปโซฟิลลา (Gypsophila)
• ดอกไม้สีขาวนวลขนาดเล็ก ให้ความรู้สึกอ่อนโยนและบริสุทธิ์
• คงรูปทรงสวยงามได้นาน ช่วยเพิ่มเลเยอร์ให้กับแจกันดอกไม้
• ตกแต่งมุมห้องให้ดูละมุนตาและมีชีวิตชีวา''',
        'image': 'images/natural_products/gypsophila.png',
        'category': 'natural'
    },
    {
        'id': 38,
        'name': 'ดอกสตอร์วฟลาวเวอร์แห้ง',
        'price': 5.00,
        'description': '''☀️ ดอกสตอร์วฟลาวเวอร์ (Strawflower)
• กลีบดอกมีลักษณะพิเศษที่ให้สัมผัสเหมือนกระดาษและคงทนสูง
• โทนสีเหลืองส้มสดใส ช่วยเติมพลังงานบวกให้กับพื้นที่
• นิยมใช้ประดับในงานฝีมือและงาน DIY ต่างๆ''',
        'image': 'images/natural_products/strawflower.png',
        'category': 'natural'
    },
    {
        'id': 39,
        'name': 'ลาเวนเดอร์แห้ง',
        'price': 5.00,
        'description': '''💜 ลาเวนเดอร์แห้ง (Lavender)
• กลิ่นหอมสะอาดที่เป็นเอกลักษณ์ ช่วยให้รู้สึกผ่อนคลาย
• มอบบรรยากาศสไตล์ทุ่งดอกไม้ในยุโรปให้กับบ้านคุณ
• สามารถวางไว้ในห้องนอนเพื่อช่วยให้การพักผ่อนดีขึ้น''',
        'image': 'images/natural_products/dried_lavender.png',
        'category': 'natural'
    },
    {
        'id': 40,
        'name': 'กุหลาบแห้ง',
        'price': 5.00,
        'description': '''🌹 ดอกกุหลาบแห้ง (Dried Rose)
• คัดสรรดอกกุหลาบสีแดงเข้มทรงสวย นำมาผ่านกระบวนการอบแห้งอย่างประณีต
• เก็บรักษาความคลาสสิกและเสน่ห์ของกุหลาบไว้ได้ยาวนาน
• สื่อถึงความรักที่เป็นอมตะ เหมาะสำหรับโอกาสพิเศษ''',
        'image': 'images/natural_products/dried_rose.png',
        'category': 'flowers'
    },
    {
        'id': 41,
        'name': 'ไฮเดรนเยียแห้ง',
        'price': 5.00,
        'description': '''🌸 ดอกไฮเดรนเยียแห้ง (Hydrangea)
• ช่อดอกขนาดใหญ่ที่มีเอกลักษณ์เฉพาะตัว
• โทนสีตุ่นสวยงาม เหมาะกับการตกแต่งสไตล์คาเฟ่หรือโฮมมี่
• ช่วยสร้างจุดดึงดูดสายตาให้กับแจกันใบโปรดของคุณ''',
        'image': 'images/natural_products/dried_hydrangea.png',
        'category': 'natural'
    },
    {
        'id': 42,
        'name': 'โรสแมรี่แห้ง',
        'price': 5.00,
        'description': '''🌿 โรสแมรี่แห้ง (Dried Rosemary)
• กลิ่นหอมสมุนไพรที่ช่วยให้รู้สึกสดชื่นและปลอดโปร่ง
• นอกจากความสวยงามยังให้กลิ่นอายธรรมชาติที่ผ่อนคลาย
• ประดับตกแต่งช่อดอกไม้หรือวางในครัวเพื่อความสวยงาม''',
        'image': 'images/natural_products/dried_rosemary.png',
        'category': 'natural'
    }
]

# ใน store/views.py

def cart(request):
    return render(request, 'cart.html')

def home(request):
    return render(request, 'home.html')

def shop(request):
    # ส่งข้อมูลสินค้าทั้งหมดไปที่หน้า Shop
    return render(request, 'shop.html', {'products': ALL_PRODUCTS})

def product_detail(request, product_id):
    # ค้นหาสินค้าจาก ID ใน list ข้างบน
    product = next((item for item in ALL_PRODUCTS if item['id'] == product_id), None)
    
    if product is None:
        raise Http404("ไม่พบสินค้านี้")

    # (Optional) หาสินค้าแนะนำ โดยเอาตัวอื่นที่ไม่ใช่ตัวปัจจุบัน
    related_products = [p for p in ALL_PRODUCTS if p['id'] != product_id][:4]

    context = {
        'product': product,
        'related_products': related_products
    }
    return render(request, 'product_detail.html', context)


def plot_detail(request):
    return render(request, 'plot_detail.html')
# --- Views อื่นๆ คงเดิม ---
def veggie_plots(request):
    return render(request, 'veggie_plots.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def process_booking(request):
    if request.method == 'POST':
        # 1. รับค่าที่ส่งมาจาก Hidden Input
        plant_name = request.POST.get('selected_plant')
        start_date_str = request.POST.get('start_date') # จะได้เป็นข้อความเช่น '2026-03-18'
        
        if plant_name and start_date_str:
            # 2. แปลงข้อความวันที่ให้เป็น Object Date ของ Python
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
            # 3. คำนวณวันเก็บเกี่ยวและราคาใหม่ที่ฝั่ง Backend (ทำ Dictionary เก็บจำนวนวันไว้ฝั่งนี้ด้วย)
            plant_grow_times = {
                "มะเขือเทศ": 75,
                "แครอท": 75,
                # ... ใส่ให้ครบเหมือนใน JS ...
            }
            
            days_needed = plant_grow_times.get(plant_name, 0)
            price_per_day = 5
            total_price = days_needed * price_per_day
            
            harvest_date = start_date + timedelta(days=days_needed)
            
            # 4. นำข้อมูลไปบันทึกลง Database (Models) 
            # Booking.objects.create(plant=plant_name, start_date=start_date, end_date=harvest_date, price=total_price)
            
            # 5. ส่งกลับไปหน้ายืนยันการจอง หรือหน้าสำเร็จ
            return render(request, 'booking_success.html', {
                'plant': plant_name,
                'start_date': start_date,
                'harvest_date': harvest_date,
                'price': total_price
            })
            
    # ถ้าไม่ใช่ POST วิ่งกลับไปหน้าเดิม
    return redirect('your_booking_page')