"""A hand-built evaluation set for Arabic name matching.

GROUPS      every pair of spellings inside a group is the same name  (positives)
DISTINCT    pairs that look or sound alike but are different names   (negatives)

Pairs from two different groups are also used as negatives.

This set was written by the project authors, who also tuned the matcher, so
treat the numbers as a regression benchmark rather than an independent
evaluation. Pull requests adding real-world pairs are very welcome.
"""

GROUPS = [
    ["محمد", "Mohammed", "Muhammad", "Mohamed", "Mohamad", "Muhammed", "Mouhamed", "מוחמד"],
    ["أحمد", "احمد", "Ahmed", "Ahmad", "Ahmet", "אחמד"],
    ["محمود", "Mahmoud", "Mahmud", "Mahmood", "מחמוד"],
    ["حسن", "Hassan", "Hasan", "Hacene", "חסן"],
    ["حسين", "Hussein", "Hussain", "Husayn", "Hossein", "Hocine", "חוסיין"],
    ["علي", "Ali", "Aly", "עלי"],
    ["عمر", "Omar", "Umar", "Omer", "עומר"],
    ["عثمان", "Othman", "Uthman", "Osman", "Otman"],
    ["يوسف", "Yousef", "Youssef", "Yusuf", "Yousuf", "Youcef", "יוסף"],
    ["إبراهيم", "ابراهيم", "Ibrahim", "Ebrahim", "Brahim", "אברהים"],
    ["خالد", "Khaled", "Khalid", "ח'אלד"],
    ["عبد الرحمن", "عبدالرحمن", "Abdulrahman", "Abdul Rahman", "Abd al-Rahman", "Abdel Rahman",
     "Abderrahmane", "Abdurrahman", "עבד אל-רחמן"],
    ["عبد الله", "عبدالله", "Abdullah", "Abdallah", "Abdulla", "Abd Allah", "עבדאללה"],
    ["عبد العزيز", "عبدالعزيز", "Abdulaziz", "Abdul Aziz", "Abdelaziz", "Abd El Aziz"],
    ["مصطفى", "مصطفي", "Mustafa", "Mostafa", "Mustapha", "Moustafa"],
    ["سعيد", "Said", "Saeed", "Saïd", "Saied"],
    ["طارق", "Tariq", "Tarek", "Tarik", "Tareq"],
    ["جمال", "Jamal", "Gamal", "Djamel", "ג'מאל"],
    ["فاطمة", "فاطمه", "Fatima", "Fatimah", "Fatma", "Fatema"],
    ["عائشة", "عايشة", "Aisha", "Aicha", "Aysha", "Ayesha"],
    ["خديجة", "Khadija", "Khadijah", "Khadidja", "Khadiga"],
    ["مريم", "Maryam", "Mariam", "Meriem", "Mariem"],
    ["زينب", "Zainab", "Zaynab", "Zeinab"],
    ["ليلى", "Layla", "Leila", "Laila", "Leyla"],
    ["نور الدين", "نورالدين", "Noureddine", "Nur al-Din", "Nuruddin", "Nour Eddine"],
    ["صلاح الدين", "Salahuddin", "Salah al-Din", "Salah Eddine", "Salaheddine"],
    ["أبو بكر", "ابوبكر", "Abu Bakr", "Abubakar", "Aboubakr", "Abou Bakr"],
    ["القذافي", "Qaddafi", "Gaddafi", "Kadhafi", "Gadhafi", "al-Qadhafi"],
    ["هشام", "Hisham", "Hicham", "Hesham"],
    ["وائل", "Wael", "Wail", "Wa'el"],
    ["يحيى", "يحيي", "Yahya", "Yehia", "Yahia"],
    ["داود", "داوود", "Dawud", "Dawood", "Daoud", "Daud"],
    ["شريف", "Sharif", "Sherif", "Cherif", "Shareef"],
    ["محمد علي حسن", "Mohamed Ali Hassan", "Muhammad Aly Hasan", "Hassan, Mohamed Ali", "מוחמד עלי חסן"],
    ["أحمد عبد الله السيد", "Ahmed Abdullah El-Sayed", "Ahmad Abdallah Elsayed", "Dr. Ahmed Abdullah Al Sayed"],
    ["فاطمة الزهراء محمد", "Fatima Zahra Mohamed", "Fatima al-Zahra Muhammad", "Fatma Ezzahra Mohammed"],
    ["خالد بن الوليد", "Khalid ibn al-Walid", "Khaled Bin Alwaleed", "Khalid Al Walid"],
    ["يوسف عبد الرحمن الخطيب", "Yousef Abdulrahman Al-Khatib", "Youssef Abdel Rahman El Khatib"],
    ["عمر حسين الحداد", "Omar Hussein Haddad", "Umar Husayn al-Haddad", "Omer Hussain Alhaddad"],
    ["نادية كريم", "Nadia Karim", "Nadiya Kareem", "Nadia Kerim"],
]

DISTINCT = [
    ("حسن", "حسين"), ("Hassan", "Hussein"), ("حسن", "Hussein"), ("حسين", "Hasan"),
    ("محمد", "محمود"), ("Mohamed", "Mahmoud"), ("محمد", "Mahmoud"), ("محمود", "Mohammed"),
    ("أحمد", "حمد"), ("Ahmed", "Hamad"), ("أحمد", "Hamid"), ("Ahmad", "Hamed"),
    ("خالد", "خليل"), ("Khalid", "Khalil"), ("خالد", "Khalil"),
    ("سعيد", "سعد"), ("Said", "Saad"), ("سعيد", "سعود"), ("Saeed", "Saud"), ("سعيد", "سيد"),
    ("سالم", "سلمان"), ("Salim", "Salman"), ("سليم", "سليمان"), ("Salim", "Sulayman"),
    ("عمر", "عمرو"), ("Omar", "Amr"), ("عمر", "عمار"), ("Omar", "Ammar"), ("عامر", "عمر"),
    ("علي", "علا"), ("Ali", "Alaa"), ("علي", "Alia"),
    ("جمال", "جميل"), ("Jamal", "Jamil"), ("جمال", "كمال"), ("Jamal", "Kamal"),
    ("كريم", "أكرم"), ("Karim", "Akram"),
    ("ناصر", "نصر"), ("Nasser", "Nasr"), ("نصر", "نزار"),
    ("ياسر", "ياسين"), ("Yasser", "Yassin"),
    ("زيد", "زياد"), ("Zaid", "Ziad"),
    ("راشد", "رشاد"), ("Rashid", "Rashad"), ("رشيد", "رشدي"),
    ("مريم", "مروان"), ("Maryam", "Marwan"), ("Marwa", "Marwan"),
    ("سمير", "سميرة"), ("Samir", "Samira"), ("أمين", "أمينة"), ("Amin", "Amina"),
    ("فاطمة", "فاتن"), ("Fatima", "Fatin"), ("هدى", "هند"), ("Huda", "Hind"),
    ("منى", "مها"), ("Mona", "Maha"), ("نور", "نورة"), ("Nour", "Noura"),
    ("عبد الرحمن", "عبد الرحيم"), ("Abdul Rahman", "Abdul Rahim"), ("Abdulrahman", "Abdulrahim"),
    ("عبد الله", "عبد الإله"), ("Abdullah", "Abdulaziz"), ("عبد العزيز", "عبد العظيم"),
    ("عبد الكريم", "عبد الحكيم"), ("Abdelkarim", "Abdelhakim"),
    ("يوسف", "يونس"), ("Yusuf", "Yunus"), ("موسى", "عيسى"), ("Musa", "Isa"),
    ("طارق", "طلال"), ("Tariq", "Tawfiq"), ("هشام", "هاشم"), ("Hisham", "Hashim"),
    ("إبراهيم", "إسماعيل"), ("Ibrahim", "Ismail"),
    ("محمد علي", "محمد حسن"), ("Mohamed Ali", "Mohamed Hassan"), ("Mohamed Ali", "Ahmed Ali"),
    ("أحمد محمد علي", "أحمد حسن علي"), ("Ahmed Mohamed Ali", "Ahmed Mahmoud Ali"),
    ("Omar Hussein Haddad", "Omar Hassan Haddad"), ("خالد يوسف", "خليل يوسف"),
    ("Fatima Ali", "Fatima Aly Hassan Ibrahim Khalil"), ("Nadia Karim", "Nadia Kamil"),
    ("Yousef Al-Khatib", "Yousef Al-Khalil"), ("صلاح الدين", "نور الدين"),
    ("Salahuddin", "Nuruddin"), ("أبو بكر", "أبو عمر"), ("Abu Bakr", "Abu Omar"),
]
