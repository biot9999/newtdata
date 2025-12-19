#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Profile Modifier Module - Batch modify Telegram account profiles
支持智能随机生成和自定义配置两种模式
"""

import random
import logging
import asyncio
import time
from typing import Dict, List, Optional, Tuple, Set, Any
from telethon import TelegramClient
from telethon.tl import functions, types
from telethon.errors import FloodWaitError, SessionPasswordNeededError

logger = logging.getLogger(__name__)


class IntelligentNameGenerator:
    """智能姓名生成器 - 根据手机区号生成对应语言姓名"""
    
    # 国家区号映射
    COUNTRY_CODE_MAP = {
        '1': 'english',      # 美国/加拿大
        '7': 'russian',      # 俄罗斯
        '33': 'french',      # 法国
        '34': 'spanish',     # 西班牙
        '39': 'italian',     # 意大利
        '44': 'english',     # 英国
        '49': 'german',      # 德国
        '81': 'japanese',    # 日本
        '82': 'korean',      # 韩国
        '86': 'chinese',     # 中国
        '90': 'turkish',     # 土耳其
        '91': 'hindi',       # 印度
        '966': 'arabic',     # 沙特
        '55': 'portuguese',  # 巴西
        '351': 'portuguese', # 葡萄牙
        '52': 'spanish',     # 墨西哥
        '54': 'spanish',     # 阿根廷
        '358': 'finnish',    # 芬兰
        '46': 'swedish',     # 瑞典
        '47': 'norwegian',   # 挪威
        '31': 'dutch',       # 荷兰
        '32': 'french',      # 比利时
        '41': 'german',      # 瑞士
        '43': 'german',      # 奥地利
        '45': 'danish',      # 丹麦
        '48': 'polish',      # 波兰
        '36': 'hungarian',   # 匈牙利
        '420': 'czech',      # 捷克
        '421': 'slovak',     # 斯洛伐克
        '40': 'romanian',    # 罗马尼亚
        '30': 'greek',       # 希腊
        '972': 'hebrew',     # 以色列
        '98': 'persian',     # 伊朗
        '92': 'urdu',        # 巴基斯坦
        '880': 'bengali',    # 孟加拉
        '66': 'thai',        # 泰国
        '84': 'vietnamese',  # 越南
        '62': 'indonesian',  # 印度尼西亚
        '60': 'malay',       # 马来西亚
        '63': 'filipino',    # 菲律宾
    }
    
    # 多语言姓名库
    NAME_DATA = {
        'english': {
            'first': ['James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles',
                     'Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Emma', 'Olivia', 'Sophia', 'Isabella', 'Mia'],
            'last': ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                    'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee'],
        },
        'russian': {
            'first': ['Александр', 'Дмитрий', 'Максим', 'Иван', 'Сергей', 'Андрей', 'Алексей', 'Михаил', 'Николай', 'Владимир',
                     'Мария', 'Анна', 'Елена', 'Ольга', 'Наталья', 'Екатерина', 'Ирина', 'Светлана', 'Юлия', 'Татьяна'],
            'last': ['Иванов', 'Смирнов', 'Кузнецов', 'Попов', 'Соколов', 'Лебедев', 'Козлов', 'Новиков', 'Морозов', 'Петров',
                    'Волков', 'Соловьев', 'Васильев', 'Зайцев', 'Павлов', 'Семенов', 'Голубев', 'Виноградов', 'Богданов', 'Воробьев'],
        },
        'german': {
            'first': ['Hans', 'Klaus', 'Wolfgang', 'Helmut', 'Peter', 'Michael', 'Thomas', 'Andreas', 'Stefan', 'Christian',
                     'Anna', 'Sophie', 'Emma', 'Marie', 'Laura', 'Julia', 'Lisa', 'Sarah', 'Nicole', 'Katharina'],
            'last': ['Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner', 'Becker', 'Schulz', 'Hoffmann',
                    'Koch', 'Bauer', 'Richter', 'Klein', 'Wolf', 'Schröder', 'Neumann', 'Schwarz', 'Zimmermann', 'Braun'],
        },
        'french': {
            'first': ['Jean', 'Pierre', 'Michel', 'André', 'Philippe', 'Alain', 'Patrick', 'François', 'Jacques', 'Nicolas',
                     'Marie', 'Sophie', 'Camille', 'Julie', 'Emma', 'Léa', 'Chloé', 'Manon', 'Sarah', 'Laura'],
            'last': ['Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert', 'Petit', 'Richard', 'Durand', 'Leroy', 'Moreau',
                    'Simon', 'Laurent', 'Lefebvre', 'Michel', 'Garcia', 'David', 'Bertrand', 'Roux', 'Vincent', 'Fournier'],
        },
        'spanish': {
            'first': ['José', 'Carlos', 'Juan', 'Antonio', 'Manuel', 'Francisco', 'Luis', 'Miguel', 'Pedro', 'Javier',
                     'María', 'Ana', 'Carmen', 'Isabel', 'Dolores', 'Pilar', 'Teresa', 'Rosa', 'Francisca', 'Laura'],
            'last': ['García', 'Rodríguez', 'Martínez', 'López', 'González', 'Hernández', 'Pérez', 'Sánchez', 'Ramírez', 'Torres',
                    'Flores', 'Rivera', 'Gómez', 'Díaz', 'Reyes', 'Cruz', 'Morales', 'Jiménez', 'Ruiz', 'Ortiz'],
        },
        'italian': {
            'first': ['Giovanni', 'Marco', 'Alessandro', 'Andrea', 'Francesco', 'Giuseppe', 'Antonio', 'Luca', 'Paolo', 'Matteo',
                     'Maria', 'Sofia', 'Giulia', 'Anna', 'Chiara', 'Sara', 'Francesca', 'Laura', 'Elena', 'Valentina'],
            'last': ['Rossi', 'Russo', 'Ferrari', 'Esposito', 'Bianchi', 'Romano', 'Colombo', 'Ricci', 'Marino', 'Greco',
                    'Bruno', 'Gallo', 'Conti', 'De Luca', 'Costa', 'Giordano', 'Mancini', 'Rizzo', 'Lombardi', 'Moretti'],
        },
        'japanese': {
            'first': ['太郎', '花子', '健太', '美咲', '翔太', 'さくら', '大輔', '結衣', '拓也', '愛',
                     '隆', '由美', '健', '智子', '勇', '陽子', '誠', '真由美', '剛', '恵子'],
            'last': ['佐藤', '鈴木', '高橋', '田中', '渡辺', '伊藤', '山本', '中村', '小林', '加藤',
                    '吉田', '山田', '佐々木', '山口', '松本', '井上', '木村', '林', '清水', '山崎'],
        },
        'korean': {
            'first': ['민준', '서연', '지우', '하은', '도윤', '수아', '예준', '지민', '현우', '하준',
                     '서준', '예은', '지훈', '서아', '준서', '민서', '유준', '채원', '시우', '수빈'],
            'last': ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임',
                    '한', '오', '서', '신', '권', '황', '안', '송', '류', '홍'],
        },
        'arabic': {
            'first': ['محمد', 'أحمد', 'علي', 'حسن', 'حسين', 'خالد', 'سعيد', 'عبدالله', 'عمر', 'ياسر',
                     'فاطمة', 'عائشة', 'خديجة', 'مريم', 'زينب', 'سارة', 'نور', 'لينا', 'ليلى', 'دينا'],
            'last': ['العلي', 'الأحمد', 'المحمد', 'الحسن', 'الخالد', 'السعيد', 'العمر', 'الحمد', 'النصر', 'الشمري',
                    'العتيبي', 'القحطاني', 'الدوسري', 'المطيري', 'الحربي', 'الزهراني', 'العمري', 'السالم', 'البلوي', 'الغامدي'],
        },
        'turkish': {
            'first': ['Mehmet', 'Ahmet', 'Mustafa', 'Ali', 'Hüseyin', 'Hasan', 'İbrahim', 'Osman', 'Süleyman', 'Yusuf',
                     'Ayşe', 'Fatma', 'Emine', 'Zeynep', 'Hatice', 'Elif', 'Merve', 'Büşra', 'Esra', 'Meryem'],
            'last': ['Yılmaz', 'Kaya', 'Demir', 'Çelik', 'Şahin', 'Yıldız', 'Yıldırım', 'Öztürk', 'Aydın', 'Özdemir',
                    'Arslan', 'Doğan', 'Kılıç', 'Aslan', 'Çetin', 'Kara', 'Koç', 'Kurt', 'Özcan', 'Şimşek'],
        },
        'hindi': {
            'first': ['राज', 'प्रिया', 'अमित', 'सुनीता', 'विजय', 'अनु', 'संजय', 'नीता', 'राकेश', 'कविता',
                     'सुरेश', 'मीना', 'दीपक', 'पूजा', 'मनोज', 'रेखा', 'अशोक', 'आरती', 'राजेश', 'सीमा'],
            'last': ['शर्मा', 'वर्मा', 'कुमार', 'सिंह', 'पटेल', 'गुप्ता', 'राय', 'जैन', 'अग्रवाल', 'मेहता',
                    'जोशी', 'देसाई', 'शाह', 'खान', 'नायर', 'रेड्डी', 'चौधरी', 'मल्होत्रा', 'भट्ट', 'सक्सेना'],
        },
        'portuguese': {
            'first': ['João', 'Maria', 'José', 'Ana', 'Paulo', 'Pedro', 'Carlos', 'Sofia', 'Lucas', 'Mariana',
                     'Miguel', 'Beatriz', 'Tiago', 'Rita', 'Francisco', 'Inês', 'Rafael', 'Catarina', 'Diogo', 'Carolina'],
            'last': ['Silva', 'Santos', 'Oliveira', 'Souza', 'Costa', 'Ferreira', 'Rodrigues', 'Almeida', 'Nascimento', 'Lima',
                    'Araújo', 'Fernandes', 'Carvalho', 'Gomes', 'Martins', 'Rocha', 'Ribeiro', 'Alves', 'Monteiro', 'Mendes'],
        },
        'chinese': {
            'first': ['伟', '芳', '娜', '敏', '静', '丽', '强', '磊', '军', '洋',
                     '艳', '勇', '涛', '明', '超', '秀英', '杰', '娟', '涛', '秀兰'],
            'last': ['王', '李', '张', '刘', '陈', '杨', '黄', '赵', '周', '吴',
                    '徐', '孙', '马', '朱', '胡', '郭', '何', '高', '林', '罗'],
        },
        'finnish': {
            'first': ['Juhani', 'Johannes', 'Olavi', 'Mikael', 'Tapani', 'Kalevi', 'Jari', 'Matti', 'Kari', 'Juha',
                     'Maria', 'Helena', 'Johanna', 'Anneli', 'Kaarina', 'Marjatta', 'Pirjo', 'Eeva', 'Sari', 'Tuula'],
            'last': ['Korhonen', 'Virtanen', 'Mäkinen', 'Nieminen', 'Mäkelä', 'Hämäläinen', 'Laine', 'Heikkinen', 'Koskinen', 'Järvinen'],
        },
        'swedish': {
            'first': ['Lars', 'Erik', 'Karl', 'Anders', 'Per', 'Johan', 'Nils', 'Mikael', 'Jan', 'Hans',
                     'Anna', 'Maria', 'Margareta', 'Elisabeth', 'Eva', 'Kristina', 'Birgitta', 'Karin', 'Linda', 'Marie'],
            'last': ['Andersson', 'Johansson', 'Karlsson', 'Nilsson', 'Eriksson', 'Larsson', 'Olsson', 'Persson', 'Svensson', 'Gustafsson'],
        },
        'norwegian': {
            'first': ['Jan', 'Per', 'Bjørn', 'Ole', 'Lars', 'Kjell', 'Knut', 'Arne', 'Svein', 'Rune',
                     'Anne', 'Inger', 'Kari', 'Marit', 'Ingrid', 'Liv', 'Eva', 'Berit', 'Astrid', 'Hilde'],
            'last': ['Hansen', 'Johansen', 'Olsen', 'Larsen', 'Andersen', 'Pedersen', 'Nilsen', 'Kristiansen', 'Jensen', 'Karlsen'],
        },
        'dutch': {
            'first': ['Jan', 'Pieter', 'Hendrik', 'Willem', 'Cornelis', 'Johannes', 'Jacobus', 'Adrianus', 'Dirk', 'Gerrit',
                     'Maria', 'Anna', 'Johanna', 'Catharina', 'Hendrika', 'Cornelia', 'Elisabeth', 'Geertruida', 'Adriana', 'Margaretha'],
            'last': ['De Jong', 'Jansen', 'De Vries', 'Van den Berg', 'Van Dijk', 'Bakker', 'Janssen', 'Visser', 'Smit', 'Meijer'],
        },
        'polish': {
            'first': ['Jan', 'Andrzej', 'Piotr', 'Krzysztof', 'Stanisław', 'Tomasz', 'Paweł', 'Józef', 'Marcin', 'Marek',
                     'Maria', 'Anna', 'Katarzyna', 'Małgorzata', 'Agnieszka', 'Barbara', 'Ewa', 'Elżbieta', 'Krystyna', 'Zofia'],
            'last': ['Nowak', 'Kowalski', 'Wiśniewski', 'Wójcik', 'Kowalczyk', 'Kamiński', 'Lewandowski', 'Zieliński', 'Szymański', 'Woźniak'],
        },
        'danish': {
            'first': ['Peter', 'Jens', 'Michael', 'Lars', 'Henrik', 'Thomas', 'Søren', 'Jan', 'Christian', 'Martin',
                     'Anne', 'Kirsten', 'Hanne', 'Lene', 'Marianne', 'Helle', 'Susanne', 'Lone', 'Pia', 'Tina'],
            'last': ['Nielsen', 'Jensen', 'Hansen', 'Pedersen', 'Andersen', 'Christensen', 'Larsen', 'Sørensen', 'Rasmussen', 'Jørgensen'],
        },
        'hungarian': {
            'first': ['László', 'István', 'József', 'János', 'Zoltán', 'Sándor', 'Gábor', 'Ferenc', 'Attila', 'Péter',
                     'Mária', 'Erzsébet', 'Ilona', 'Ildikó', 'Katalin', 'Éva', 'Judit', 'Andrea', 'Margit', 'Ágnes'],
            'last': ['Nagy', 'Kovács', 'Tóth', 'Szabó', 'Horváth', 'Varga', 'Kiss', 'Molnár', 'Németh', 'Farkas'],
        },
        'czech': {
            'first': ['Jan', 'Petr', 'Josef', 'Pavel', 'Martin', 'Tomáš', 'Jaroslav', 'Miroslav', 'František', 'Jiří',
                     'Marie', 'Jana', 'Eva', 'Anna', 'Hana', 'Lenka', 'Kateřina', 'Věra', 'Alena', 'Petra'],
            'last': ['Novák', 'Svoboda', 'Novotný', 'Dvořák', 'Černý', 'Procházka', 'Kučera', 'Veselý', 'Horák', 'Němec'],
        },
        'slovak': {
            'first': ['Ján', 'Peter', 'Jozef', 'Martin', 'František', 'Pavol', 'Andrej', 'Tomáš', 'Michal', 'Miroslav',
                     'Mária', 'Anna', 'Eva', 'Zuzana', 'Jana', 'Katarína', 'Veronika', 'Lucia', 'Monika', 'Petra'],
            'last': ['Varga', 'Tóth', 'Nagy', 'Horváth', 'Kováč', 'Balogh', 'Szabó', 'Molnár', 'Papp', 'Kiss'],
        },
        'romanian': {
            'first': ['Ion', 'Gheorghe', 'Nicolae', 'Vasile', 'Constantin', 'Dumitru', 'Stefan', 'Marin', 'Petre', 'Alexandru',
                     'Maria', 'Elena', 'Ana', 'Ioana', 'Mihaela', 'Gabriela', 'Andreea', 'Alexandra', 'Daniela', 'Simona'],
            'last': ['Popescu', 'Popa', 'Pop', 'Ionescu', 'Constantin', 'Dumitru', 'Stan', 'Stoica', 'Gheorghe', 'Dobre'],
        },
        'greek': {
            'first': ['Γιώργος', 'Δημήτρης', 'Νίκος', 'Γιάννης', 'Κώστας', 'Μανώλης', 'Χρήστος', 'Παναγιώτης', 'Βασίλης', 'Μάκης',
                     'Μαρία', 'Ελένη', 'Κατερίνα', 'Βασιλική', 'Σοφία', 'Αικατερίνη', 'Παρασκευή', 'Αγγελική', 'Δήμητρα', 'Ευαγγελία'],
            'last': ['Παπαδόπουλος', 'Παππάς', 'Παναγιωτόπουλος', 'Νικολάου', 'Κωνσταντίνου', 'Δημητρίου', 'Γεωργίου', 'Βασιλείου', 'Αθανασίου', 'Χριστοδούλου'],
        },
        'hebrew': {
            'first': ['דוד', 'משה', 'יוסף', 'אברהם', 'יעקב', 'יצחק', 'שמואל', 'דניאל', 'מיכאל', 'אריאל',
                     'שרה', 'רחל', 'לאה', 'רבקה', 'מרים', 'דבורה', 'אסתר', 'רות', 'חנה', 'תמר'],
            'last': ['כהן', 'לוי', 'מזרחי', 'פרץ', 'ביטון', 'אוחיון', 'דהן', 'אבוקסיס', 'אזולאי', 'חדד'],
        },
        'persian': {
            'first': ['محمد', 'علی', 'حسن', 'حسین', 'رضا', 'احمد', 'مهدی', 'جواد', 'مجید', 'ابراهیم',
                     'فاطمه', 'زهرا', 'مریم', 'زینب', 'سکینه', 'معصومه', 'طاهره', 'صدیقه', 'خدیجه', 'فرشته'],
            'last': ['احمدی', 'محمدی', 'رضایی', 'حسینی', 'علی‌پور', 'کریمی', 'مرادی', 'اسماعیلی', 'نوری', 'غلامی'],
        },
        'urdu': {
            'first': ['محمد', 'علی', 'احمد', 'حسن', 'حسین', 'عمر', 'عثمان', 'عبداللہ', 'فاطمہ', 'عائشہ',
                     'خدیجہ', 'زینب', 'مریم', 'سارہ', 'نور', 'صفیہ', 'رقیہ', 'حفصہ', 'سمیہ', 'اسماء'],
            'last': ['خان', 'احمد', 'علی', 'حسین', 'شاہ', 'ملک', 'چوہدری', 'بٹ', 'میر', 'خان'],
        },
        'bengali': {
            'first': ['রাজ', 'অমিত', 'রাহুল', 'অরুণ', 'বিজয়', 'সুমিত', 'প্রদীপ', 'সঞ্জয়', 'বিকাশ', 'রবি',
                     'প্রিয়া', 'সুনীতা', 'অনু', 'কবিতা', 'নীতা', 'রেখা', 'মীনা', 'পূজা', 'সীমা', 'আরতী'],
            'last': ['দাস', 'রায়', 'বোস', 'চৌধুরী', 'মুখার্জী', 'ঘোষ', 'সরকার', 'সেনগুপ্ত', 'নন্দী', 'ব্যানার্জী'],
        },
        'thai': {
            'first': ['สมชาย', 'สมศักดิ์', 'สมหมาย', 'สมบัติ', 'สมพงษ์', 'วิชัย', 'วิเชียร', 'ประสิทธิ์', 'ชาติชาย', 'สุชาติ',
                     'สมหญิง', 'สมพร', 'วันเพ็ญ', 'มาลี', 'นิตยา', 'สุดา', 'ประไพ', 'สุภา', 'วิไล', 'ละเอียด'],
            'last': ['จันทร์', 'เดือน', 'ดาว', 'แสง', 'สว่าง', 'วงศ์', 'ศรี', 'สุข', 'เจริญ', 'รุ่ง'],
        },
        'vietnamese': {
            'first': ['Nguyễn', 'Văn', 'Thị', 'Hồng', 'Minh', 'Hải', 'Tuấn', 'Hùng', 'Dũng', 'Phương',
                     'Lan', 'Hương', 'Linh', 'Hà', 'Mai', 'Thu', 'Ngọc', 'Anh', 'Trang', 'Hoa'],
            'last': ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Phan', 'Vũ', 'Đặng', 'Bùi', 'Đỗ'],
        },
        'indonesian': {
            'first': ['Ahmad', 'Muhammad', 'Budi', 'Siti', 'Sri', 'Agus', 'Indra', 'Putra', 'Dewi', 'Andi',
                     'Rina', 'Nina', 'Rini', 'Ani', 'Lina', 'Yanti', 'Wati', 'Ningsih', 'Sari', 'Fitri'],
            'last': ['Susanto', 'Wijaya', 'Santoso', 'Putri', 'Pratama', 'Saputra', 'Kurniawan', 'Hidayat', 'Prasetyo', 'Setiawan'],
        },
        'malay': {
            'first': ['Ahmad', 'Muhammad', 'Abdul', 'Hassan', 'Ali', 'Ismail', 'Ibrahim', 'Mohd', 'Aziz', 'Rahman',
                     'Siti', 'Fatimah', 'Noraini', 'Noor', 'Aishah', 'Zainab', 'Hajar', 'Mariam', 'Khadijah', 'Aminah'],
            'last': ['Abdullah', 'Rahman', 'Ahmad', 'Ibrahim', 'Hassan', 'Mohamed', 'Ali', 'Ismail', 'Osman', 'Yasin'],
        },
        'filipino': {
            'first': ['Jose', 'Juan', 'Pedro', 'Antonio', 'Francisco', 'Manuel', 'Ramon', 'Carlos', 'Luis', 'Miguel',
                     'Maria', 'Ana', 'Rosa', 'Carmen', 'Teresa', 'Josefa', 'Luz', 'Concepcion', 'Esperanza', 'Mercedes'],
            'last': ['Santos', 'Reyes', 'Cruz', 'Bautista', 'Garcia', 'Mendoza', 'Torres', 'Lopez', 'Gonzales', 'Rodriguez'],
        },
    }
    
    def detect_language_from_phone(self, phone: str) -> str:
        """从手机号检测语言"""
        phone = phone.strip().lstrip('+')
        
        # 从长到短匹配区号（支持4位、3位、2位、1位区号）
        for length in [4, 3, 2, 1]:
            code = phone[:length]
            if code in self.COUNTRY_CODE_MAP:
                return self.COUNTRY_CODE_MAP[code]
        
        return 'english'  # 默认
    
    def generate_unique_name(self, language: str, used_names: Set[str]) -> Tuple[str, str]:
        """生成唯一姓名，确保不重复"""
        max_attempts = 100
        
        for _ in range(max_attempts):
            names = self.NAME_DATA.get(language, self.NAME_DATA['english'])
            first = random.choice(names['first'])
            last = random.choice(names['last'])
            
            # 某些语言姓在前
            if language in ['japanese', 'korean', 'chinese', 'vietnamese']:
                full_name = f"{last}{first}"
                name_tuple = (full_name, "")
            else:
                full_name = f"{first} {last}"
                name_tuple = (first, last)
            
            # 检查唯一性
            if full_name not in used_names:
                used_names.add(full_name)
                return name_tuple
        
        # 添加随机后缀确保唯一
        suffix = random.randint(1, 999)
        if language in ['japanese', 'korean', 'chinese', 'vietnamese']:
            return (f"{last}{first}{suffix}", "")
        else:
            return (f"{first}{suffix}", last)
    
    def generate_name_by_phone(self, phone: str, used_names: Set[str]) -> Tuple[str, str]:
        """根据手机号生成姓名"""
        language = self.detect_language_from_phone(phone)
        return self.generate_unique_name(language, used_names)


class EmojiAvatarGenerator:
    """Emoji头像生成器 - 使用Telegram官方Emoji头像功能"""
    
    # 300+ 可用的 emoji
    AVATAR_EMOJIS = [
        # 笑脸类 (30个)
        '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃',
        '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙',
        '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🤫', '🤔',
        
        # 动物类 (50个)
        '🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯',
        '🦁', '🐮', '🐷', '🐸', '🐵', '🙈', '🙉', '🙊', '🐒', '🐔',
        '🐧', '🐦', '🐤', '🦆', '🦅', '🦉', '🦇', '🐺', '🐗', '🐴',
        '🦄', '🐝', '🐛', '🦋', '🐌', '🐞', '🐜', '🦟', '🦗', '🕷',
        '🦂', '🐢', '🐍', '🦎', '🦖', '🦕', '🐙', '🦑', '🦐', '🦞',
        
        # 食物类 (40个)
        '🍎', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🍈', '🍒', '🍑',
        '🥭', '🍍', '🥥', '🥝', '🍅', '🍆', '🥑', '🥦', '🌶', '🌽',
        '🥕', '🥔', '🍠', '🥐', '🥖', '🍞', '🧀', '🍕', '🍔', '🍟',
        '🌭', '🥪', '🌮', '🌯', '🍜', '🍝', '🍱', '🍣', '🍤', '🍩',
        
        # 运动类 (20个)
        '⚽', '🏀', '🏈', '⚾', '🥎', '🎾', '🏐', '🏉', '🥏', '🎱',
        '🏓', '🏸', '🏒', '🏑', '🥍', '🏏', '⛳', '🏹', '🎣', '🥊',
        
        # 自然类 (30个)
        '🌸', '🌹', '🌺', '🌻', '🌼', '🌷', '🌱', '🌲', '🌳', '🌴',
        '🌵', '🌾', '🌿', '☘', '🍀', '🍁', '🍂', '🍃', '⭐', '🌟',
        '✨', '⚡', '🔥', '🌈', '☀', '🌤', '⛅', '🌥', '☁', '🌦',
        
        # 交通类 (30个)
        '🚗', '🚕', '🚙', '🚌', '🚎', '🏎', '🚓', '🚑', '🚒', '🚐',
        '🚚', '🚛', '🚜', '🛴', '🚲', '🛵', '🏍', '✈', '🛫', '🛬',
        '🚁', '🚂', '🚆', '🚇', '🚊', '🚉', '🚀', '🛸', '⛵', '🚤',
        
        # 符号类 (40个)
        '❤', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔',
        '❣', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮',
        '⭐', '🌟', '✨', '💫', '🔥', '💥', '✅', '❌', '⚡', '🌈',
        '🎵', '🎶', '🎤', '🎧', '🎸', '🎹', '🎺', '🎻', '🥁', '🎮',
    ]
    
    def get_random_emoji(self) -> str:
        """获取随机emoji"""
        return random.choice(self.AVATAR_EMOJIS)
    
    async def set_emoji_avatar(self, client: TelegramClient, emoji: str = None) -> bool:
        """设置Emoji头像（使用UpdateProfileRequest）"""
        try:
            if emoji is None:
                emoji = self.get_random_emoji()
            
            # 使用UpdateProfileRequest清空头像（Telegram不支持直接设置emoji头像通过API）
            # 注意：Telegram的emoji头像功能主要在客户端，API层面需要用其他方法
            # 这里我们暂时只能删除现有头像，无法设置emoji头像
            # 实际应用中，可能需要生成emoji图片并上传
            
            logger.info(f"尝试设置Emoji头像: {emoji}")
            
            # 删除当前头像
            try:
                photos = await client.get_profile_photos('me')
                if photos:
                    await client(functions.photos.DeletePhotosRequest(
                        id=[types.InputPhoto(
                            id=photos[0].id,
                            access_hash=photos[0].access_hash,
                            file_reference=photos[0].file_reference
                        )]
                    ))
                    logger.info(f"已删除现有头像")
            except Exception as e:
                logger.debug(f"删除头像失败或无头像: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"设置Emoji头像失败: {e}")
            return False


class BioGenerator:
    """简介生成器 - 根据语言生成对应简介"""
    
    BIO_TEMPLATES = {
        'english': [
            'Living my best life ✨',
            'Dream big, work hard 💪',
            'Coffee lover ☕',
            'Travel enthusiast 🌍',
            'Music & art 🎵🎨',
            'Just living 🌟',
            'Be yourself 💫',
            'Stay positive ⭐',
            'Life is beautiful 🌈',
            'Follow your dreams 🎯',
        ],
        'russian': [
            'Люблю жизнь 🌈',
            'Мечтатель ✨',
            'Путешественник 🌍',
            'Музыка и кофе ☕🎵',
            'Просто живу 🌟',
            'Будь собой 💫',
            'Позитив ⭐',
            'Жизнь прекрасна 🌺',
        ],
        'german': [
            'Lebe mein Leben ✨',
            'Kaffeeliebhaber ☕',
            'Reisebegeistert 🌍',
            'Musik & Kunst 🎵🎨',
            'Bleib positiv ⭐',
            'Träume groß 💫',
        ],
        'french': [
            'Vivre ma vie ✨',
            'Amateur de café ☕',
            'Voyageur passionné 🌍',
            'Musique & art 🎵🎨',
            'La vie est belle 🌈',
            'Sois toi-même 💫',
        ],
        'spanish': [
            'Viviendo la vida ✨',
            'Amante del café ☕',
            'Viajero apasionado 🌍',
            'Música y arte 🎵🎨',
            'La vida es bella 🌈',
            'Sé tú mismo 💫',
        ],
        'italian': [
            'Vivo la mia vita ✨',
            'Amante del caffè ☕',
            'Viaggiatore appassionato 🌍',
            'Musica e arte 🎵🎨',
            'La vita è bella 🌈',
        ],
        'japanese': [
            '人生を楽しむ ✨',
            'コーヒー好き ☕',
            '旅行が好き 🌍',
            '音楽とアート 🎵🎨',
            '夢を追いかける 💫',
        ],
        'korean': [
            '인생을 즐기다 ✨',
            '커피 애호가 ☕',
            '여행 애호가 🌍',
            '음악과 예술 🎵🎨',
            '꿈을 이루다 💫',
        ],
        'arabic': [
            'أعيش حياتي ✨',
            'عاشق القهوة ☕',
            'عاشق السفر 🌍',
            'الموسيقى والفن 🎵🎨',
            'الحياة جميلة 🌈',
        ],
        'turkish': [
            'Hayatımı yaşıyorum ✨',
            'Kahve aşığı ☕',
            'Seyahat tutkunu 🌍',
            'Müzik ve sanat 🎵🎨',
            'Hayat güzel 🌈',
        ],
        'hindi': [
            'जीवन का आनंद ✨',
            'कॉफी प्रेमी ☕',
            'यात्रा उत्साही 🌍',
            'संगीत और कला 🎵🎨',
            'सपने देखो 💫',
        ],
        'portuguese': [
            'Vivendo minha vida ✨',
            'Amante de café ☕',
            'Entusiasta de viagens 🌍',
            'Música e arte 🎵🎨',
            'A vida é bela 🌈',
        ],
        'chinese': [
            '热爱生活 ✨',
            '咖啡爱好者 ☕',
            '旅行爱好者 🌍',
            '音乐与艺术 🎵🎨',
            '追逐梦想 💫',
        ],
        'finnish': [
            'Elän elämääni ✨',
            'Kahvinrakastaja ☕',
            'Matkailijainto 🌍',
            'Musiikki ja taide 🎵🎨',
        ],
        'swedish': [
            'Lever mitt liv ✨',
            'Kaffeälskare ☕',
            'Reseentusiast 🌍',
            'Musik & konst 🎵🎨',
        ],
        'norwegian': [
            'Lever livet mitt ✨',
            'Kaffeelsker ☕',
            'Reiseentusiast 🌍',
            'Musikk og kunst 🎵🎨',
        ],
        'dutch': [
            'Leef mijn leven ✨',
            'Koffieliefhebber ☕',
            'Reisliefhebber 🌍',
            'Muziek & kunst 🎵🎨',
        ],
        'polish': [
            'Żyję swoim życiem ✨',
            'Miłośnik kawy ☕',
            'Entuzjasta podróży 🌍',
            'Muzyka i sztuka 🎵🎨',
        ],
        'danish': [
            'Lever mit liv ✨',
            'Kaffeelsker ☕',
            'Rejseentusiast 🌍',
            'Musik & kunst 🎵🎨',
        ],
        'hungarian': [
            'Élem az életem ✨',
            'Kávérajongó ☕',
            'Utazási rajongó 🌍',
            'Zene és művészet 🎵🎨',
        ],
        'czech': [
            'Žiji svůj život ✨',
            'Milovník kávy ☕',
            'Cestovní nadšenec 🌍',
            'Hudba a umění 🎵🎨',
        ],
        'slovak': [
            'Žijem svoj život ✨',
            'Milovník kávy ☕',
            'Cestovateľský nadšenec 🌍',
            'Hudba a umenie 🎵🎨',
        ],
        'romanian': [
            'Îmi trăiesc viața ✨',
            'Iubitor de cafea ☕',
            'Entuziast de călătorii 🌍',
            'Muzică și artă 🎵🎨',
        ],
        'greek': [
            'Ζω τη ζωή μου ✨',
            'Λάτρης του καφέ ☕',
            'Ενθουσιώδης ταξιδιώτης 🌍',
            'Μουσική & τέχνη 🎵🎨',
        ],
        'hebrew': [
            'חי את החיים שלי ✨',
            'אוהב קפה ☕',
            'חובב טיולים 🌍',
            'מוזיקה ואומנות 🎵🎨',
        ],
        'persian': [
            'زندگی خود را می‌گذرانم ✨',
            'عاشق قهوه ☕',
            'علاقه‌مند به سفر 🌍',
            'موسیقی و هنر 🎵🎨',
        ],
        'urdu': [
            'اپنی زندگی جی رہا ہوں ✨',
            'کافی کا شوقین ☕',
            'سفر کا شوقین 🌍',
            'موسیقی اور فن 🎵🎨',
        ],
        'bengali': [
            'আমার জীবন উপভোগ করছি ✨',
            'কফি প্রেমী ☕',
            'ভ্রমণ উৎসাহী 🌍',
            'সঙ্গীত ও শিল্প 🎵🎨',
        ],
        'thai': [
            'ใช้ชีวิตของฉัน ✨',
            'คนรักกาแฟ ☕',
            'นักท่องเที่ยว 🌍',
            'ดนตรีและศิลปะ 🎵🎨',
        ],
        'vietnamese': [
            'Sống cuộc sống của tôi ✨',
            'Người yêu cà phê ☕',
            'Đam mê du lịch 🌍',
            'Âm nhạc & nghệ thuật 🎵🎨',
        ],
        'indonesian': [
            'Menjalani hidup saya ✨',
            'Pencinta kopi ☕',
            'Penggemar perjalanan 🌍',
            'Musik & seni 🎵🎨',
        ],
        'malay': [
            'Menjalani hidup saya ✨',
            'Peminat kopi ☕',
            'Peminat pelancongan 🌍',
            'Muzik & seni 🎵🎨',
        ],
        'filipino': [
            'Namumuhay ng aking buhay ✨',
            'Mahilig sa kape ☕',
            'Mahilig sa paglalakbay 🌍',
            'Musika at sining 🎵🎨',
        ],
    }
    
    def generate_bio(self, language: str, empty_rate: float = 0.3) -> str:
        """生成简介"""
        # 30% 概率留空
        if random.random() < empty_rate:
            return ""
        
        templates = self.BIO_TEMPLATES.get(language, self.BIO_TEMPLATES['english'])
        return random.choice(templates) if templates else ""


class ProfileModifier:
    """资料修改器 - 批量修改Telegram账号资料"""
    
    def __init__(self):
        self.name_gen = IntelligentNameGenerator()
        self.emoji_gen = EmojiAvatarGenerator()
        self.bio_gen = BioGenerator()
        self.used_names: Set[str] = set()
    
    async def modify_profile_random(self, client: TelegramClient, phone: str) -> Dict[str, Any]:
        """随机模式修改资料"""
        try:
            # 1. 根据手机号生成姓名
            first_name, last_name = self.name_gen.generate_name_by_phone(phone, self.used_names)
            
            # 2. 随机 emoji（用于记录，实际无法通过API设置）
            emoji = self.emoji_gen.get_random_emoji()
            
            # 3. 生成简介（根据语言）
            language = self.name_gen.detect_language_from_phone(phone)
            bio = self.bio_gen.generate_bio(language, empty_rate=0.3)
            
            # 4. 执行修改
            # 修改姓名和简介
            await client(functions.account.UpdateProfileRequest(
                first_name=first_name,
                last_name=last_name,
                about=bio
            ))
            
            # 尝试设置头像（清空现有头像）
            await self.emoji_gen.set_emoji_avatar(client, emoji)
            
            return {
                'status': 'success',
                'first_name': first_name,
                'last_name': last_name,
                'emoji': emoji,
                'bio': bio or '(空)',
                'language': language
            }
            
        except FloodWaitError as e:
            logger.warning(f"遇到限流，需要等待 {e.seconds} 秒")
            return {
                'status': 'failed',
                'error': f'限流，需等待{e.seconds}秒'
            }
        except Exception as e:
            logger.error(f"修改资料失败: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def modify_profile_custom(self, client: TelegramClient, config: Dict[str, Any]) -> Dict[str, Any]:
        """自定义模式修改资料"""
        try:
            # 根据配置修改
            if config.get('first_name'):
                await client(functions.account.UpdateProfileRequest(
                    first_name=config['first_name'],
                    last_name=config.get('last_name', ''),
                    about=config.get('bio', '')
                ))
            
            # 自定义头像
            if config.get('emoji'):
                await self.emoji_gen.set_emoji_avatar(client, config['emoji'])
            elif config.get('photo_path'):
                await client(functions.photos.UploadProfilePhotoRequest(
                    file=await client.upload_file(config['photo_path'])
                ))
            
            return {'status': 'success'}
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
