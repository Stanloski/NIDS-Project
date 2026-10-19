import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from pathlib import Path

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def create_layman_defense_doc(output_path):
    doc = docx.Document()
    
    # 1 inch margins
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    PRIMARY = RGBColor(0, 135, 81)     # UNN Green #008751
    SECONDARY = RGBColor(30, 41, 59)   # Slate #1E293B
    TEXT_COLOR = RGBColor(51, 65, 85)  # Neutral Text
    MUTED = RGBColor(100, 116, 139)
    GOLD = RGBColor(180, 83, 9)        # Deep Amber/Gold

    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = TEXT_COLOR
    normal_style.paragraph_format.line_spacing = 1.2
    normal_style.paragraph_format.space_after = Pt(6)

    def add_title(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(22)
        run.font.color.rgb = PRIMARY
        return p

    def add_subtitle(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(18)
        run = p.add_run(text)
        run.italic = True
        run.font.size = Pt(12)
        run.font.color.rgb = MUTED
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(8)
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(15)
        run.font.color.rgb = PRIMARY
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(12.5)
        run.font.color.rgb = SECONDARY
        return p

    def add_speech_box(spoken_text, context_label="EXACT WORDS TO SAY OUT LOUD:"):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.cell(0, 0)
        set_cell_background(cell, "F0FDF4") # soft green
        set_cell_margins(cell, top=140, bottom=140, left=200, right=200)

        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(4)
        head = p.add_run(f"🗣️ {context_label}\n")
        head.bold = True
        head.font.size = Pt(10)
        head.font.color.rgb = PRIMARY

        body = p.add_run(f'"{spoken_text}"')
        body.italic = True
        body.font.size = Pt(11)
        body.font.color.rgb = SECONDARY

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    def add_analogy_box(analogy_text, title="💡 THE SIMPLE EVERYDAY ANALOGY (Think of it like this):"):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.cell(0, 0)
        set_cell_background(cell, "FEF3C7") # soft warm gold
        set_cell_margins(cell, top=120, bottom=120, left=180, right=180)

        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(4)
        head = p.add_run(f"{title}\n")
        head.bold = True
        head.font.size = Pt(10)
        head.font.color.rgb = GOLD

        body = p.add_run(analogy_text)
        body.font.size = Pt(10.5)
        body.font.color.rgb = SECONDARY

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ---------------- DOCUMENT CONTENT ----------------
    add_title("NIDS PROJECT DEFENSE GUIDE (LAYMAN'S EDITION)")
    add_subtitle("How to Defend Your Project in Plain, Simple English\nDepartment of Computer Science • University of Nigeria, Nsukka (UNN)")

    # Metadata Box
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Project Topic:", "Design and Implementation of a Network Intrusion Detection System Using Random Forest Machine Learning Algorithm"),
        ("Presenter / Candidate:", "Okafor Ugochukwu Stanley (Reg No: 2022/249519)"),
        ("Group Members (Group 2):", "Okafor Michael Osinachi, Okafor Ugochukwu Stanley, Okechukwu Daniel Somtochukwu"),
        ("Supervisor:", "Dr. U.K Umeh | Academic Year: 2026")
    ]
    for i, (k, v) in enumerate(meta_data):
        row = meta_table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.3)
        set_cell_background(c0, "F8FAFC")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, 70, 70, 90, 90)
        set_cell_margins(c1, 70, 70, 90, 90)
        
        p0 = c0.paragraphs[0]; p0.paragraph_format.space_after = Pt(2)
        r0 = p0.add_run(k); r0.bold = True; r0.font.size = Pt(9.5); r0.font.color.rgb = SECONDARY

        p1 = c1.paragraphs[0]; p1.paragraph_format.space_after = Pt(2)
        r1 = p1.add_run(v); r1.font.size = Pt(9.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Section 1: What is this project really about?
    add_h1("SECTION 1: THE WHOLE PROJECT EXPLAINED IN 60 SECONDS")
    p = doc.add_paragraph(
        "Before you memorize any technical words, understand what you actually built in real life:"
    )

    add_analogy_box(
        "Imagine the University of Nigeria gate. A normal firewall is like a security guard checking student ID cards. "
        "If a thief steals a genuine UNN student ID card, the security guard opens the gate and lets him in! "
        "The guard only checks the card, not what the person does afterwards.\n\n"
        "Our NIDS (Network Intrusion Detection System) is like smart CCTV cameras with AI installed all over campus. "
        "Even if you entered with a valid ID, if you start climbing into office windows at 2 AM or carrying 50 heavy bags out of the ICT center, "
        "the AI instantly notices that your BEHAVIOR is abnormal and rings the alarm bell: INTRUSION DETECTED!",
        title="💡 THE GATE GUARD VS THE SMART CCTV (Firewall vs NIDS):"
    )

    p = doc.add_paragraph(
        "In our software, instead of watching people walking around campus, our AI watches data packets flowing across network cables. "
        "It checks 41 clues per connection—like how big the message is, how fast it was sent, and whether it failed to connect. "
        "Then it tells the university IT admin: 'This packet is normal student traffic' or 'This packet is a hacker trying to attack!'"
    )

    # Section 2: Opening Pitch in Simple English
    add_h1("SECTION 2: YOUR 2-MINUTE OPENING PITCH (PRACTICE THIS OUT LOUD)")
    p = doc.add_paragraph(
        "When Dr. Umeh or the examiners look at you and say: 'Stanley, introduce your project', take one breath, smile, and say this:"
    )

    add_speech_box(
        "Good morning, Sirs and Mas. My name is Okafor Ugochukwu Stanley, presenting on behalf of Group 2. "
        "Our project is titled: Design and Implementation of a Network Intrusion Detection System Using Random Forest Machine Learning Algorithm, "
        "supervised by Dr. U.K. Umeh.\n\n"
        "In simple terms, Sir: Traditional network firewalls only look at names and port numbers. "
        "If a hacker disguises their attack as normal web browsing, the firewall lets them pass. "
        "To solve this problem, we built an intelligent watchdog for the network.\n\n"
        "Instead of relying on rigid rules, we trained an Artificial Intelligence model called Random Forest—which acts like a jury of 100 expert digital security guards—trained on over 125,000 recorded network interactions from the global NSL-KDD dataset.\n\n"
        "We then built a complete, practical web application called RADAR WATCHTOWER. It lets a network administrator monitor traffic in real-time, test single suspicious connections, upload bulk network logs, and see instant threat verdicts with over 96% precision.\n\n"
        "With your permission, I would love to show you a quick live demonstration of how it works."
    )

    # Section 3: The 4 Attacks Explained Simply
    add_h1("SECTION 3: THE 4 TYPES OF ATTACKS (IN EVERYDAY LANGUAGE)")
    p = doc.add_paragraph(
        "Examiners love asking: 'What kinds of attacks can your system catch?' "
        "Here is how to describe them so simply that anyone will understand:"
    )

    attacks_table = doc.add_table(rows=5, cols=3)
    attacks_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    att_headers = ["Attack Category", "Everyday Life Example", "What the Hacker is Doing"]
    for j, h in enumerate(att_headers):
        cell = attacks_table.cell(0, j)
        set_cell_background(cell, "008751")
        set_cell_margins(cell, 90, 90, 110, 110)
        p = cell.paragraphs[0]; p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h); r.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = RGBColor(255, 255, 255)

    att_rows = [
        ("1. DoS (Denial of Service)", 
         "Like 10,000 people rushing to enter the UNN portal at the exact same second until the website crashes and no real student can check their results.", 
         "Overwhelming the server with fake traffic so legitimate users get locked out."),
        
        ("2. Probe (Port Scanning)", 
         "Like a thief walking quietly down a hotel corridor at night, gently twisting every single door handle to see which room was left unlocked.", 
         "Testing every open port on a server to find an unpatched weakness."),
         
        ("3. R2L (Remote-to-Local)", 
         "Like an outsider standing outside the staff quarters trying 500 different master keys to open the main front door from outside.", 
         "An unauthorized remote user trying to break in and gain local access to a computer."),
         
        ("4. U2R (User-to-Root)", 
         "Like a student who is allowed inside the faculty library as a guest, but sneaks into the dean's private office to steal the exam stamp and master keys.", 
         "A regular user with basic access exploiting a bug to become the supreme administrator ('root').")
    ]

    for i, (c1, c2, c3) in enumerate(att_rows):
        row = attacks_table.rows[i + 1]
        cell0, cell1, cell2 = row.cells[0], row.cells[1], row.cells[2]
        cell0.width = Inches(1.8)
        cell1.width = Inches(2.7)
        cell2.width = Inches(2.0)
        bg = "F8FAFC" if i % 2 == 0 else "FFFFFF"
        for c in (cell0, cell1, cell2):
            set_cell_background(c, bg)
            set_cell_margins(c, 70, 70, 90, 90)
        
        p0 = cell0.paragraphs[0]; p0.paragraph_format.space_after = Pt(2)
        r0 = p0.add_run(c1); r0.bold = True; r0.font.size = Pt(9.5)

        p1 = cell1.paragraphs[0]; p1.paragraph_format.space_after = Pt(2)
        r1 = p1.add_run(c2); r1.font.size = Pt(9)

        p2 = cell2.paragraphs[0]; p2.paragraph_format.space_after = Pt(2)
        r2 = p2.add_run(c3); r2.font.size = Pt(9)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Section 4: The Machine Learning in Plain English
    add_h1("SECTION 4: THE MACHINE LEARNING CONCEPTS IN PLAIN ENGLISH")

    add_h2("What is Random Forest?")
    add_analogy_box(
        "Imagine you have a difficult medical problem. If you ask just ONE doctor, he might make a mistake or miss something. "
        "Instead, you go to a hospital board with 100 different doctors. "
        "Each doctor inspects your medical tests from a slightly different angle. "
        "At the end, all 100 doctors vote: 95 say 'healthy', 5 say 'sick'. You trust the majority vote!\n\n"
        "That is exactly what Random Forest does. It builds 100 Decision Trees. Each tree votes on whether a packet is safe or an attack. The majority vote wins.",
        title="💡 THE COUNCIL OF 100 DOCTORS (Random Forest):"
    )

    add_h2("Why 77% Accuracy is Actually Impressive (Don't let them trick you!)")
    add_analogy_box(
        "Suppose a teacher gives students 10 past question papers to study for an exam. "
        "In school A, the teacher gives the exact same past questions in the final exam. The students score 99%! But did they really learn? No, they just memorized the past questions.\n\n"
        "In school B, the examiner deliberately adds 17 BRAND NEW questions that were never seen before in any past question paper. Scoring 77% on such a tough, surprise exam proves the student truly understands the subject!\n\n"
        "In our project, we used the official benchmark dataset called KDDTest+. It intentionally includes 17 new attack types that the AI was never taught in training. 77% is the genuine, honest academic score against unknown zero-day attacks.",
        title="💡 THE UNSEEN EXAM QUESTIONS (Why 77% Accuracy is Honest Science):"
    )

    add_h2("Why 96.7% Precision is the Real Superstar Metric")
    add_analogy_box(
        "Think of a car alarm. If your car alarm screams every time a breeze blows or a cat walks past, by the third day, "
        "you and your neighbors will ignore it or turn it off. When a real thief comes, nobody cares!\n\n"
        "In cybersecurity, false alarms are dangerous. Our system achieves 96.68% Precision and only a 2.8% False Alarm rate. "
        "That means when our watchdog barks, you know with 97% certainty that someone is actually trying to steal the car!",
        title="💡 THE CRY-WOLF CAR ALARM (Why High Precision Matters):"
    )

    # Section 5: The Live Demo (What to say while clicking)
    add_h1("SECTION 5: LIVE DEMO NARRATION (WHAT TO SAY ON SCREEN)")
    p = doc.add_paragraph(
        "When you are standing in front of the laptop/projector, talk step-by-step as you click:"
    )

    demo_steps = [
        ("Action 1: Show the Login Page",
         "Say: 'Sir, notice our login screen designed with UNN green and gold branding. We protected it against password guessing: if anyone tries wrong passwords 5 times, the system locks them out for 15 minutes.' -> Click login."),
        
        ("Action 2: Show the Dashboard",
         "Say: 'This is the RADAR WATCHTOWER dashboard. It gives the network engineer a birds-eye view of everything happening right now. These cards show total traffic processed, attack percentages, and live graphs showing packet flow.'"),
         
        ("Action 3: Demonstrate Single Packet Test",
         "Say: 'Let us test a single connection manually. I will click Manual Predict. First, I click the Normal Traffic button. Notice that we have normal web browsing data. When I click Analyze, the AI votes: NORMAL traffic with high confidence.'\n\n"
         "'Now, watch what happens when I switch to the DoS Attack button. The destination bytes drop to zero, and the status flag becomes S0—meaning someone sent a request but refused to finish the connection, leaving the server hanging. I click Analyze: instantly, our system flags it in bright red: INTRUSION / ATTACK!'"),
         
        ("Action 4: Demonstrate Batch File Upload",
         "Say: 'In real universities like UNN, millions of connections happen every day. An admin cannot test packets one by one. So we built this Batch Upload tool. I will upload a file containing dozens of recorded connections. In less than one second, the system checks every single packet, sorts them, and displays which ones were attacks and which ones were safe.'"),
         
        ("Action 5: Show the Audit History",
         "Say: 'Finally, here is the History page. Every single decision made by our AI is recorded with an exact date, time, and safety verdict. The administrator can search through it or export the complete report to Excel/CSV for university management.'")
    ]

    for title, desc in demo_steps:
        add_h2(title)
        add_speech_box(desc, context_label="NARRATION:")

    # Section 6: Top 6 Questions in Layman Terms
    add_h1("SECTION 6: THE 6 MOST COMMON EXAMINER QUESTIONS (ANSWERED IN SIMPLE ENGLISH)")

    questions = [
        ("Examiner: 'Why did you use Random Forest instead of Deep Learning (like Neural Networks)?'",
         "Sir, Deep Learning models are like huge 'black boxes'—they require very expensive graphics cards (GPUs) and take longer to think before giving an answer. "
         "On a busy network where thousands of packets arrive every second, you need an answer in less than 2 milliseconds. "
         "Random Forest runs instantly on ordinary office computers, uses very little battery and CPU, and unlike neural networks, "
         "it can actually tell us WHICH clues made it choose its verdict (Explainable AI)."),
         
        ("Examiner: 'Why is your accuracy 77%? Isn't that too low?'",
         "Sir, if any student tells you they got 99% on the KDD dataset, it usually means they tested the model on the same type of data they used for training. "
         "We used the official KDDTest+ benchmark, which intentionally has 17 brand-new attack tricks that were never taught during training. "
         "More importantly, in cybersecurity, what matters most is: does the system cry wolf? Our false alarm rate is only 2.8%, and when our system warns of an attack, it is 96.7% accurate. That is what makes it practically usable in real life."),
         
        ("Examiner: 'What is the difference between this and a normal Firewall?'",
         "Sir, a Firewall is like a gate man checking ID cards at the gate. If a hacker enters through the main open gate (port 80 for internet browsing), the firewall lets him in because the gate is supposed to be open. "
         "Our NIDS is like an intelligent surveillance camera inside the building. It doesn't care which gate you used; it watches your behavior once you are inside to catch suspicious activity."),
         
        ("Examiner: 'What are the most important clues your AI looks for?'",
         "From our 100 decision trees, the top 3 clues are:\n"
         "1. Source Bytes (18.5%): How much data the sender is pushing. Attackers usually send abnormally huge or zero-byte packets.\n"
         "2. Connection Flag (13.1%): Did the conversation finish politely (SF flag), or did the sender leave the line hanging open (S0 flag)?\n"
         "3. Destination Bytes (9.9%): How much data came back in reply."),
         
        ("Examiner: 'What happens if the internet goes off or your server loses connection?'",
         "Sir, our entire system is designed to run 100% offline. All our charts, fonts, and the trained AI brain (rf_model.joblib) are stored right here on the computer. "
         "It does not require internet connection or any cloud service to inspect network packets and protect the campus."),
         
        ("Examiner: 'Stanley, what was your personal contribution to this group project?'",
         "Sir, as a key member of Group 2, I personally worked on:\n"
         "1. Training the Random Forest AI model and evaluating its performance metrics on the NSL-KDD benchmark.\n"
         "2. Building the backend server and security database in Python Flask.\n"
         "3. Designing the user interface and running the 17 automated test cases in test_suite.py to make sure the software has zero bugs.")
    ]

    for q, a in questions:
        add_h2(q)
        add_speech_box(a, context_label="YOUR DIRECT ANSWER:")

    # Section 7: Final Words of Encouragement
    add_h1("SECTION 7: STANLEY'S DEFENSE DAY SURVIVAL RULES")
    rules = [
        "Rule 1: Don't talk too fast. When we are nervous, we tend to rush. Force yourself to speak slowly and clearly. It makes you sound confident and in control.",
        "Rule 2: Don't argue with an examiner. If an examiner says: 'I think you should have added feature X', don't say 'No, that is wrong'. Say: 'That is a very good point, Sir. That is actually one of the key recommendations we highlighted for future work in Chapter 5.' (This disarms them completely!).",
        "Rule 3: Keep your laptop plugged in. Nothing is more painful than a laptop shutting down right when you are showing a demo.",
        "Rule 4: Remember: YOU built this. You know how the buttons work, you know where the files are, and you know the metrics. Walk into that room with your head high!"
    ]
    for r in rules:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(r)
        run.font.size = Pt(10.5)

    doc.save(str(output_path))
    print(f"Successfully generated Layman Edition defense guide at: {output_path}")

if __name__ == "__main__":
    out = Path(r"c:\Users\Dell\Desktop\NIDS Project\NIDS_Project_Defense_Layman_Guide.docx")
    create_layman_defense_doc(out)
    try:
        master_out = Path(r"c:\Users\Dell\Desktop\NIDS Project\NIDS_Project_Defense_Master_Guide.docx")
        create_layman_defense_doc(master_out)
    except Exception as e:
        print(f"Note: Master guide is currently open in Word ({e}), saved Layman edition separately.")
