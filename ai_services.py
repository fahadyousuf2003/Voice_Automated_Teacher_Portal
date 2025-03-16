from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.schema import AIMessage

# ------------------------------
# AI Query Processing LLAMA
# ------------------------------

def initialize_groq_qa():
    """
    Initializes the Groq LLAMA model for question-answering.
    """
    try:
        # Define prompt template
        template = """You are an AI assistant for answering queries about teacher-related tasks.
        Use the following context to answer the question at the end.
        Provide concise, accurate answers.

        Context: {context}

        Question: {question}
        Answer:"""

        prompt = PromptTemplate(
            template=template, input_variables=["context", "question"]
        )

        # Initialize Groq LLAMA
        groq_model = ChatGroq(
            model_name="llama3-8b-8192",
            api_key="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",
            temperature=0
        )

        return groq_model, prompt

    except Exception as e:
        raise RuntimeError(f"Failed to initialize Groq LLAMA: {e}")

# Initialize Groq model and prompt globally
groq_model, groq_prompt = initialize_groq_qa()


def fetch_teacher_data(question):
    """
    Uses Groq LLAMA to answer teacher-related queries.
    """
    context = """
    1. TEACHER RESPONSIBILITIES
       - Teachers must plan and conduct lessons according to the curriculum.
       - They keep track of students' progress, give feedback, and manage class discipline.
       - They communicate with parents/guardians when necessary.

    2. GRADING & ASSIGNMENTS
       - Assignments typically make up 40% of the final grade.
       - Quizzes and midterm exams make up 30%, and final exams another 30%.
       - Each assignment is graded on a 100-point scale, then weighted accordingly.
       - Late submissions incur a 10% penalty per day (up to 3 days).
       - Teachers must post grades and feedback within 7 days of submission.

    3. ATTENDANCE & PARTICIPATION
       - Attendance is recorded daily through the school's management system.
       - A student is marked "Present" if they attend at least 80% of a given session.
       - Chronic lateness or leaving early may reduce participation points.
       - Participation includes in-class discussions, group activities, and online forum contributions.

    4. CLASS SCHEDULING
       - Teachers can schedule or reschedule classes using the school portal.
       - Rescheduling requires approval from the academic coordinator if it conflicts with other classes.
       - Classrooms and time slots are assigned based on availability, class size, and any special equipment needs.

    5. EXAMS & ASSESSMENTS
       - Midterm exams usually occur in Week 8 of the semester, while final exams occur in Week 16.
       - Teachers create exam papers and must submit them to the exam board at least 2 weeks before the exam date.
       - Students with documented accommodations may receive extra time or alternative exam formats.

    6. PLAGIARISM & ACADEMIC INTEGRITY
       - All written assignments are subject to a plagiarism check.
       - A similarity score of 20% or above triggers a manual review by the teacher.
       - Confirmed plagiarism may result in a zero for the assignment and a warning letter.

    7. COMMUNICATION & NOTIFICATIONS
       - Teachers can send notifications about upcoming assignments, changes in schedule, or exam details.
       - Email reminders are typically sent 3 days before an assignment is due.
       - Parent-teacher meetings are scheduled once per semester, or on-demand if a student is struggling.

    8. PROFESSIONAL DEVELOPMENT
       - Teachers are encouraged to attend workshops and seminars to improve teaching methods.
       - Technical support is available for the school portal and virtual classroom tools.
    """

    try:
        input_data = groq_prompt.format(context=context, question=question)
        response = groq_model.invoke(input=input_data)

        # Ensure the response content is extracted correctly
        if isinstance(response, AIMessage):
            answer = response.content.strip()
        else:
            answer = str(response).strip()

        # Provide a fallback if the model can't find an answer
        if not answer:
            return "I'm not sure how to respond to that. Please ask about assignments, attendance, or classes."

        return answer

    except Exception as e:
        return f"Error processing the query: {str(e)}"


# ------------------------------
# Lecture Summarization (LLAMA)
# ------------------------------

def summarize_lecture(transcript):
    """
    Summarizes a given lecture transcript using Groq LLAMA.
    """
    prompt_text = (
        "You are an AI assistant specialized in summarizing lectures. "
        "Given the following lecture transcript, provide a concise and accurate summary.\n\n"
        "Transcript:\n"
        f"{transcript}\n\n"
        "Summary:"
    )

    try:
        response = groq_model.invoke(input=prompt_text)

        # Ensure the response content is extracted correctly
        if hasattr(response, "content"):
            summary = response.content.strip()
        else:
            summary = str(response).strip()

        if not summary:
            return "No summary could be generated. Please try again."

        return summary

    except Exception as e:
        return f"Error processing the transcript: {str(e)}"
