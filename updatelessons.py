import csv, sqlite3

# Path to the CSV file
csv_path = "tbl_lessons_export.csv"  # Replace with your CSV path if different

# Function to update/append data from CSV to tbl_lessons
def update_tbl_lessons(db_path, csv_path):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Read the CSV file
    with open(csv_path, mode="r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Check if the lesson_id already exists
            cursor.execute("SELECT * FROM tbl_lessons WHERE lesson_id = ?", (row["lesson_id"],))
            exists = cursor.fetchone()

            if exists:
                # Update the existing record
                cursor.execute(
                    """
                    UPDATE tbl_lessons
                    SET unit_id = ?, number = ?, name = ?, session_id = ?
                    WHERE lesson_id = ?
                    """,
                    (row["unit_id"], row["number"], row["name"], row["session_id"], row["lesson_id"]),
                )
            else:
                # Insert a new record
                cursor.execute(
                    """
                    INSERT INTO tbl_lessons (lesson_id, unit_id, number, name, session_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (row["lesson_id"], row["unit_id"], row["number"], row["name"], row["session_id"]),
                )

    # Commit changes and close the connection
    connection.commit()
    connection.close()

# Save the CSV data to a file for the script to use
csv_data = """lesson_id,unit_id,number,name,session_id
1,8-1,1,Features of a word processor,0
2,8-1,2,Licensing appropriate images,0
3,8-1,3,Credibility of sources,0
4,8-1,4,Researching,0
5,8-1,5,Promoting your cause,0
6,8-1,6,Project completion and assessment,0
7,8-2,1,Python - First Steps,0
8,8-2,2,Python - Crunching Numbers,0
9,8-2,3,Python - At a crossroad,0
10,8-2,4,Python - More Branches,0
11,8-2,5,Python - Round and round,0
12,8-2,6,Python - Putting it all together,0
13,8-3,1,Felt Cute Might Delete,0
14,8-3,2,Pull Down to refresh,0
15,8-3,3,No filter,0
16,8-3,4,Friend Request Pending,0
17,8-3,5,Fake News,0
18,8-3,6,Don’t Me,0
19,8-3,7,Censored,0
20,8-3,8,Test,0
21,8-4,1,Get in gear,0
22,8-4,2,Under the hood,0
23,8-4,3,Orchestra conductor,0
24,8-4,4,It’s only logical,0
25,8-4,5,Thinking Machines,0
26,8-4,6,Revision + Practical Assessment + Test,0
27,8-5,1,Top Trumps Lesson 1,0
28,8-5,2,Top Trumps Lesson 2,0
29,8-5,3,Top Trumps Lesson 3,0
30,8-5,4,Top Trumps Lesson 4,0
31,8-6,1,Wick Editor Lesson 1,0
32,8-6,2,Wick Editor Lesson 2,0
33,8-6,3,Wick Editor Lesson 3,0
34,8-6,4,Wick Editor Lesson 4,0
35,8-6,5,Wick Editor Lesson 5,0
36,8-6,6,Wick Editor Lesson 6,0
37,9-1,1,,0
38,9-1,2,,0
39,9-1,3,,0
40,9-1,4,,0
41,9-1,5,,0
42,9-1,6,,0
43,9-2,1,,0
44,9-2,2,,0
45,9-2,3,,0
46,9-2,4,,0
47,9-2,5,,0
48,9-2,6,,0
49,9-3,1,,0
50,9-3,2,,0
51,9-3,3,,0
52,9-3,4,,0
53,9-3,5,,0
54,8-2,7,Python - Revision,0
55,8-2,8,Python - Practical Assessment,0
56,8-2,9,Python - Test,0
"""
db_path="instance/flashcards.db"
with open(csv_path, "w", encoding="utf-8") as f:
    f.write(csv_data)

# Run the function to update the database
update_tbl_lessons(db_path, csv_path)
