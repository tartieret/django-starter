from importlib import import_module

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from django.urls import resolve
from django.http import HttpRequest
from django.template import Template, Context
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from .models import (
    Answer,
    Category,
    EssayQuestion,
    MCQuestion,
    Progress,
    Quiz,
    Sitting,
    SubCategory,
    TFQuestion,
)
from .views import QuizListView, CategoriesListView, QuizDetailView


User = get_user_model()


class TestCategory(TestCase):
    def setUp(self):
        self.c1 = Category.objects.new_category(name="squishy   berries")

        self.sub1 = SubCategory.objects.create(name="Red", category=self.c1)

    def test_categories(self):
        self.assertEqual(self.c1.category, "squishy-berries")

    def test_sub_categories(self):
        self.assertEqual(self.sub1.category, self.c1)


class TestQuiz(TestCase):
    def setUp(self):
        self.c1 = Category.objects.new_category(name="elderberries")

        self.quiz1 = Quiz.objects.create(
            id=1, title="test quiz 1", description="d1", url="tq1"
        )
        self.quiz2 = Quiz.objects.create(
            id=2, title="test quiz 2", description="d2", url="t q2"
        )
        self.quiz3 = Quiz.objects.create(
            id=3, title="test quiz 3", description="d3", url="t   q3"
        )
        self.quiz4 = Quiz.objects.create(
            id=4, title="test quiz 4", description="d4", url="T-!�$%^&*Q4"
        )

        self.question1 = MCQuestion.objects.create(id=1, content="squawk")
        self.question1.quiz.add(self.quiz1)

    def test_quiz_url(self):
        self.assertEqual(self.quiz1.url, "tq1")
        self.assertEqual(self.quiz2.url, "t-q2")
        self.assertEqual(self.quiz3.url, "t-q3")
        self.assertEqual(self.quiz4.url, "t-q4")

    def test_quiz_options(self):
        q5 = Quiz.objects.create(
            id=5,
            title="test quiz 5",
            description="d5",
            url="tq5",
            category=self.c1,
            exam_paper=True,
        )

        self.assertEqual(q5.category.name, self.c1.name)
        self.assertEqual(q5.random_order, False)
        self.assertEqual(q5.exam_paper, True)

    def test_quiz_single_attempt(self):
        self.quiz1.single_attempt = True
        self.quiz1.save()

        self.assertEqual(self.quiz1.exam_paper, True)

    def test_get_max_score(self):
        self.assertEqual(self.quiz1.get_max_score, 1)

    def test_get_questions(self):
        self.assertIn(self.question1, self.quiz1.get_questions())

    def test_pass_mark(self):
        self.assertEqual(self.quiz1.pass_mark, False)
        self.quiz1.pass_mark = 50
        self.assertEqual(self.quiz1.pass_mark, 50)
        self.quiz1.pass_mark = 101
        with self.assertRaises(ValidationError):
            self.quiz1.save()


class TestProgress(TestCase):
    def setUp(self):
        self.c1 = Category.objects.new_category(name="elderberries")

        self.quiz1 = Quiz.objects.create(
            id=1, title="test quiz 1", description="d1", url="tq1"
        )

        self.question1 = MCQuestion.objects.create(content="squawk", category=self.c1)

        self.user = User.objects.create_user(
            email="jacob@jacob.com", password="top_secret"
        )

        self.p1 = Progress.objects.new_progress(self.user)

    def test_list_all_empty(self):
        self.assertEqual(self.p1.score, "")

        category_dict = self.p1.list_all_cat_scores

        self.assertIn(str(list(category_dict.keys())[0]), self.p1.score)

        self.assertIn(self.c1.category, self.p1.score)

        Category.objects.new_category(name="cheese")

        self.p1.list_all_cat_scores

        self.assertIn("cheese", self.p1.score)

    def test_subcategory_all_empty(self):
        SubCategory.objects.create(sub_category="pickles", category=self.c1)
        # self.p1.list_all_cat_scores
        # self.assertIn('pickles', self.p1.score)
        # TODO: test after implementing subcategory scoring on progress page

    def test_update_score(self):
        self.p1.list_all_cat_scores
        self.p1.update_score(self.question1, 1, 2)
        self.assertIn("elderberries", self.p1.list_all_cat_scores)

        cheese = Category.objects.new_category(name="cheese")
        question2 = MCQuestion.objects.create(content="squeek", category=cheese)
        self.p1.update_score(question2, 3, 4)

        self.assertIn("cheese", self.p1.list_all_cat_scores)
        self.assertEqual([3, 4, 75], self.p1.list_all_cat_scores["cheese"])

        # pass in string instead of question instance
        with self.assertRaises(AttributeError):
            self.p1.update_score("hamster", 3, 4)

        non_int = self.p1.update_score(question2, "1", 2)
        self.assertIn(_("error"), non_int)

        # negative possible score
        self.p1.update_score(question2, 0, -1)
        self.assertEqual([3, 5, 60], self.p1.list_all_cat_scores["cheese"])

        # negative added score
        self.p1.update_score(question2, -1, 1)
        self.assertEqual([4, 6, 67], self.p1.list_all_cat_scores["cheese"])


class TestSitting(TestCase):
    def setUp(self):
        self.quiz1 = Quiz.objects.create(
            id=1,
            title="test quiz 1",
            description="d1",
            url="tq1",
            pass_mark=50,
            success_text="Well done",
            fail_text="Bad luck",
        )

        self.question1 = MCQuestion.objects.create(id=1, content="squawk")
        self.question1.quiz.add(self.quiz1)

        self.answer1 = Answer.objects.create(
            id=123, question=self.question1, content="bing", correct=False
        )

        self.question2 = MCQuestion.objects.create(id=2, content="squeek")
        self.question2.quiz.add(self.quiz1)

        self.answer2 = Answer.objects.create(
            id=456, question=self.question2, content="bong", correct=True
        )

        self.user = User.objects.create_user(
            email="jacob@jacob.com", password="top_secret"
        )

        self.sitting = Sitting.objects.new_sitting(self.user, self.quiz1)

    def test_max_questions_subsetting(self):
        quiz2 = Quiz.objects.create(
            id=2, title="test quiz 2", description="d2", url="tq2", max_questions=1
        )
        self.question1.quiz.add(quiz2)
        self.question2.quiz.add(quiz2)
        sub_sitting = Sitting.objects.new_sitting(self.user, quiz2)

        self.assertNotIn("2", sub_sitting.question_list)

    def test_get_next_remove_first(self):
        self.assertEqual(self.sitting.get_first_question(), self.question1)

        self.sitting.remove_first_question()
        self.assertEqual(self.sitting.get_first_question(), self.question2)

        self.sitting.remove_first_question()
        self.assertEqual(self.sitting.get_first_question(), False)

        self.sitting.remove_first_question()
        self.assertEqual(self.sitting.get_first_question(), False)

    def test_scoring(self):
        self.assertEqual(self.sitting.get_current_score, 0)
        self.assertEqual(self.sitting.check_if_passed, False)
        self.assertEqual(self.sitting.result_message, "Bad luck")

        self.sitting.add_to_score(1)
        self.assertEqual(self.sitting.get_current_score, 1)
        self.assertEqual(self.sitting.get_percent_correct, 50)

        self.sitting.add_to_score(1)
        self.assertEqual(self.sitting.get_current_score, 2)
        self.assertEqual(self.sitting.get_percent_correct, 100)

        self.sitting.add_to_score(1)
        self.assertEqual(self.sitting.get_current_score, 3)
        self.assertEqual(self.sitting.get_percent_correct, 100)

        self.assertEqual(self.sitting.check_if_passed, True)
        self.assertEqual(self.sitting.result_message, "Well done")

    def test_incorrect_and_complete(self):
        self.assertEqual(self.sitting.get_incorrect_questions, [])

        self.sitting.add_incorrect_question(self.question1)
        self.assertIn(1, self.sitting.get_incorrect_questions)

        question3 = TFQuestion.objects.create(id=3, content="oink")
        self.sitting.add_incorrect_question(question3)
        self.assertIn(3, self.sitting.get_incorrect_questions)

        self.assertEqual(self.sitting.complete, False)
        self.sitting.mark_quiz_complete()
        self.assertEqual(self.sitting.complete, True)

        self.assertEqual(self.sitting.current_score, 0)
        self.sitting.add_incorrect_question(self.question2)
        self.assertEqual(self.sitting.current_score, -1)

    def test_add_user_answer(self):
        guess = "123"
        self.sitting.add_user_answer(self.question1, guess)

        self.assertIn("123", self.sitting.user_answers)

    def test_return_questions_with_answers(self):
        """
        Also tests sitting.get_questions(with_answers=True)
        """
        self.sitting.add_user_answer(self.question1, "123")
        self.sitting.add_user_answer(self.question2, "456")

        user_answers = self.sitting.questions_with_user_answers
        self.assertEqual("123", user_answers[self.question1])
        self.assertEqual("456", user_answers[self.question2])

    def test_remove_incorrect_answer(self):
        self.sitting.add_incorrect_question(self.question1)
        self.sitting.add_incorrect_question(self.question2)
        self.sitting.remove_incorrect_question(self.question1)
        self.assertEqual(self.sitting.incorrect_questions, "2")
        self.assertEqual(self.sitting.current_score, 1)

    def test_return_user_sitting(self):
        via_manager = Sitting.objects.user_sitting(self.user, self.quiz1)
        self.assertEqual(self.sitting, via_manager)

    def test_progress_tracker(self):
        self.assertEqual(self.sitting.progress(), (0, 2))
        self.sitting.add_user_answer(self.question1, "123")
        self.assertEqual(self.sitting.progress(), (1, 2))


class TestNonQuestionViews(TestCase):
    """
    Starting on views not directly involved with questions.
    """

    urls = "quiz.urls"

    def setUp(self):
        self.c1 = Category.objects.new_category(name="elderberries")
        self.c2 = Category.objects.new_category(name="straw.berries")
        self.c3 = Category.objects.new_category(name="black berries")

        self.quiz1 = Quiz.objects.create(
            id=1,
            title="test quiz 1",
            description="d1",
            url="tq1",
            category=self.c1,
            single_attempt=True,
        )
        self.quiz2 = Quiz.objects.create(
            id=2, title="test quiz 2", description="d2", url="t q2"
        )

    def test_index(self):
        # unit
        view = QuizListView()
        self.assertEqual(view.get_queryset().count(), 2)

        # integration test
        response = self.client.get("/")
        self.assertContains(response, "test quiz 1")
        self.assertTemplateUsed("quiz_list.html")

    def test_index_with_drafts(self):
        self.quiz3 = Quiz.objects.create(
            id=3, title="test quiz 3", description="draft", url="draft", draft=True
        )

        view = QuizListView()
        self.assertEqual(view.get_queryset().count(), 2)

    def test_list_categories(self):
        # unit
        view = CategoriesListView()
        self.assertEqual(view.get_queryset().count(), 3)

        # integration test
        response = self.client.get("/category/")

        self.assertContains(response, "elderberries")
        self.assertContains(response, "straw.berries")
        self.assertContains(response, "black-berries")

    def test_view_cat(self):
        # unit
        view = CategoriesListView()
        self.assertEqual(view.get_queryset().count(), 3)

        # integration test
        response = self.client.get("/category/elderberries/")

        self.assertContains(response, "test quiz 1")
        self.assertNotContains(response, "test quiz 2")

    def test_progress_user(self):
        user = User.objects.create_user(email="jacob@jacob.com", password="top_secret")
        question1 = MCQuestion.objects.create(content="squawk", category=self.c1)

        self.client.login(email="jacob@jacob.com", password="top_secret")
        p1 = Progress.objects.new_progress(user)
        p1.update_score(question1, 1, 2)

        response = self.client.get("/progress/")

        self.assertContains(response, "elderberries")
        self.assertIn("straw.berries", response.context["cat_scores"])
        self.assertEqual([1, 2, 50], response.context["cat_scores"]["elderberries"])

    def test_quiz_start_page(self):
        # unit
        view = QuizDetailView()
        view.kwargs = dict(slug="tq1")
        self.assertEqual(view.get_object().category, self.c1)

        # integration test
        response = self.client.get("/tq1/")

        self.assertContains(response, "d1")
        self.assertContains(response, "attempt")
        self.assertContains(response, 'href="/tq1/take/"')
        self.assertTemplateUsed(response, "quiz/quiz_detail.html")


class TestQuestionMarking(TestCase):
    urls = "quiz.urls"

    def setUp(self):
        self.c1 = Category.objects.new_category(name="elderberries")
        self.student = User.objects.create_user(
            email="luke@rebels.com", password="top_secret"
        )
        self.teacher = User.objects.create_user(
            email="yoda@jedis.com", password="use_d@_force"
        )
        self.teacher.user_permissions.add(
            Permission.objects.get(codename="view_sittings")
        )

        self.quiz1 = Quiz.objects.create(
            id=1,
            title="test quiz 1",
            description="d1",
            url="tq1",
            category=self.c1,
            single_attempt=True,
        )
        self.quiz2 = Quiz.objects.create(
            id=2,
            title="test quiz 2",
            description="d2",
            url="tq2",
            category=self.c1,
            single_attempt=True,
        )

        self.question1 = MCQuestion.objects.create(id=1, content="squawk")
        self.question1.quiz.add(self.quiz1)

        self.question2 = MCQuestion.objects.create(id=2, content="shriek")
        self.question2.quiz.add(self.quiz2)

        self.answer1 = Answer.objects.create(
            id=123, question=self.question1, content="bing", correct=False
        )

        sitting1 = Sitting.objects.new_sitting(self.student, self.quiz1)
        sitting2 = Sitting.objects.new_sitting(self.student, self.quiz2)
        sitting1.complete = True
        sitting1.incorrect_questions = "1"
        sitting1.save()
        sitting2.complete = True
        sitting2.save()

        sitting1.add_user_answer(self.question1, "123")

    def test_paper_marking_list_view(self):
        response = self.client.get("/marking/")
        self.assertRedirects(
            response,
            "/accounts/login/?next=/marking/",
            status_code=302,
            target_status_code=404 or 200,
        )

        self.assertFalse(self.teacher.has_perm("view_sittings", self.student))

        self.client.login(email="luke@rebels.com", password="top_secret")
        response = self.client.get("/marking/")
        self.assertRedirects(
            response,
            "/accounts/login/?next=/marking/",
            status_code=302,
            target_status_code=404 or 200,
        )

        self.client.login(email="yoda@jedis.com", password="use_d@_force")
        response = self.client.get("/marking/")
        self.assertContains(response, "test quiz 1")
        self.assertContains(response, "test quiz 2")
        self.assertContains(response, "luke")

    def test_paper_marking_list_view_filter_user(self):
        new_student = User.objects.create_user(
            email="chewy@rebels.com", password="maaaawwwww"
        )
        chewy_sitting = Sitting.objects.new_sitting(new_student, self.quiz1)
        chewy_sitting.complete = True
        chewy_sitting.save()

        self.client.login(email="yoda@jedis.com", password="use_d@_force")
        response = self.client.get("/marking/", {"user_filter": "Hans"})

        self.assertNotContains(response, "chewy")
        self.assertNotContains(response, "luke")

        response = self.client.get("/marking/", {"user_filter": "chewy"})

        self.assertContains(response, "chewy")
        self.assertNotContains(response, "luke")

    def test_paper_marking_list_view_filter_quiz(self):
        self.client.login(email="yoda@jedis.com", password="use_d@_force")
        response = self.client.get("/marking/", {"quiz_filter": "1"})

        self.assertContains(response, "quiz 1")
        self.assertNotContains(response, "quiz 2")

    def test_paper_marking_detail_view(self):
        self.client.login(email="yoda@jedis.com", password="use_d@_force")
        response = self.client.get("/marking/1/")

        self.assertContains(response, "test quiz 1")
        self.assertContains(response, "squawk")
        self.assertContains(response, "incorrect")

    def test_paper_marking_detail_toggle_correct(self):
        question2 = EssayQuestion.objects.create(id=3, content="scribble")
        question2.quiz.add(self.quiz1)

        sitting3 = Sitting.objects.new_sitting(self.student, self.quiz1)
        sitting3.complete = True
        sitting3.incorrect_questions = "1,2,3"
        sitting3.add_user_answer(self.question1, "123")
        sitting3.add_user_answer(question2, "Blah blah blah")
        sitting3.save()

        self.client.login(email="yoda@jedis.com", password="use_d@_force")
        response = self.client.get("/marking/3/")
        self.assertContains(response, "button")
        self.assertNotContains(response, "Correct")

        response = self.client.post("/marking/3/", {"qid": 3})
        self.assertContains(response, "Correct")

        response = self.client.post("/marking/3/", {"qid": 3})
        self.assertNotContains(response, "Correct")


class TestQuestionViewsUser(TestCase):
    urls = "quiz.urls"

    def setUp(self):
        self.c1 = Category.objects.new_category(name="elderberries")

        self.quiz1 = Quiz.objects.create(
            id=1,
            title="test quiz 1",
            description="d1",
            url="tq1",
            category=self.c1,
            pass_mark=50,
            success_text="You have passed",
        )

        self.quiz2 = Quiz.objects.create(
            id=2,
            title="test quiz 2",
            description="d2",
            url="tq2",
            category=self.c1,
            exam_paper=True,
        )

        self.user = User.objects.create_user(
            email="jacob@jacob.com", password="top_secret"
        )

        self.quiz_writer = User.objects.create_user(
            email="writer@x.com", password="secret_top"
        )

        self.question1 = MCQuestion.objects.create(id=1, content="squawk")
        self.question1.quiz.add(self.quiz1)
        self.question1.quiz.add(self.quiz2)

        self.question2 = MCQuestion.objects.create(id=2, content="squeek")
        self.question2.quiz.add(self.quiz1)

        self.question3 = TFQuestion.objects.create(id=3, content="oink", correct=True)
        self.question3.quiz.add(self.quiz2)

        self.answer1 = Answer.objects.create(
            id=123, question=self.question1, content="bing", correct=False
        )

        self.answer2 = Answer.objects.create(
            id=456, question=self.question2, content="bong", correct=True
        )

    def test_quiz_take_user_view_only(self):
        sittings_before = Sitting.objects.count()
        self.assertEqual(sittings_before, 0)

        self.client.login(email="jacob@jacob.com", password="top_secret")
        response = self.client.get("/tq1/take/")
        sitting = Sitting.objects.get(quiz=self.quiz1)
        sittings_after = Sitting.objects.count()

        self.assertEqual(sittings_after, 1)
        self.assertEqual(sitting.user.email, "jacob@jacob.com")
        self.assertEqual(sitting.question_list, "1,2,")
        self.assertEqual(sitting.current_score, 0)
        self.assertEqual(response.context["quiz"].id, self.quiz1.id)
        self.assertEqual(response.context["question"].content, self.question1.content)
        self.assertNotIn("previous", response.context)
        self.assertTemplateUsed("question.html")

        response = self.client.get("/tq1/take/")
        sittings_after = Sitting.objects.count()

        self.assertEqual(sittings_after, 1)  # new sitting not made

        Sitting.objects.new_sitting(sitting.user, self.quiz1)

        self.assertEqual(Sitting.objects.count(), 2)

        response = self.client.get("/tq1/take/")
        sitting = Sitting.objects.filter(quiz=self.quiz1)[0]
        self.assertEqual(sitting.question_list, "1,2,")

    def test_quiz_take_user_submit(self):
        self.client.login(email="jacob@jacob.com", password="top_secret")
        response = self.client.get("/tq1/take/")
        progress_count = Progress.objects.count()

        self.assertNotContains(response, "previous question")
        self.assertEqual(progress_count, 0)

        next_question = Sitting.objects.get(quiz=self.quiz1).get_first_question()

        response = self.client.post(
            "/tq1/take/", {"answers": "123", "question_id": next_question.id}
        )

        sitting = Sitting.objects.get(quiz=self.quiz1)
        progress_count = Progress.objects.count()
        progress = Progress.objects.get(user=sitting.user).list_all_cat_scores

        self.assertContains(response, "previous question", status_code=200)
        self.assertEqual(sitting.current_score, 0)
        self.assertEqual(sitting.incorrect_questions, "1,")
        self.assertEqual(sitting.complete, False)
        self.assertEqual(progress_count, 1)
        self.assertIn(self.c1.category, progress)
        self.assertEqual(sitting.question_list, "2,")
        self.assertIn("123", response.context["previous"]["previous_answer"])
        self.assertEqual(response.context["question"].content, self.question2.content)
        self.assertTemplateUsed("question.html")

        response = self.client.post("/tq1/take/", {"answers": "456", "question_id": 2})

        self.assertEqual(Sitting.objects.count(), 0)
        self.assertTemplateUsed("result.html")
        self.assertEqual(response.context["score"], 1)
        self.assertContains(response, "You have passed")

    def test_quiz_take_user_answer_end(self):
        self.client.login(email="jacob@jacob.com", password="top_secret")
        response = self.client.post("/tq2/take/", {"answers": "123", "question_id": 1})
        self.assertNotContains(response, "previous question")

        response = self.client.post("/tq2/take/", {"answers": True, "question_id": 3})

        self.assertEqual(response.context["score"], 1)
        self.assertEqual(response.context["max_score"], 2)
        self.assertEqual(response.context["percent"], 50)
        self.assertIn(self.question1, response.context["questions"])
        self.assertIn(self.question3, response.context["questions"])

        self.assertContains(response, "above question incorrectly")
        self.assertContains(response, "True")

        sitting = Sitting.objects.get(quiz=self.quiz2, user=self.user)
        progress = Progress.objects.get(user=self.user)

        # test that exam_paper = True prevents sitting deletion
        self.assertEqual(Sitting.objects.count(), 1)
        # test that exam result can be recalled later
        self.assertIn(sitting, progress.show_exams())

    def test_user_cannot_sit_single_attempt(self):
        self.quiz2.single_attempt = True
        self.quiz2.save()
        self.client.login(email="jacob@jacob.com", password="top_secret")
        response = self.client.post("/tq2/take/", {"answers": "123", "question_id": 1})
        response = self.client.post("/tq2/take/", {"answers": True, "question_id": 3})

        # quiz complete, trying it again
        response = self.client.get("/tq2/take/")

        self.assertContains(response, "only one sitting is permitted.")
        self.assertTemplateUsed("single_complete.html")

    def test_normal_user_cannot_view_draft_quiz(self):
        Quiz.objects.create(
            id=10, title="draft quiz", description="draft", url="draft", draft=True
        )

        self.client.login(email="writer@x.com", password="secret_top")

        # load without permission
        response_without_perm = self.client.get("/draft/")
        self.assertEqual(response_without_perm.status_code, 403)

        # load with permission
        self.quiz_writer.user_permissions.add(
            Permission.objects.get(codename="change_quiz")
        )
        response_with_perm = self.client.get("/draft/")
        self.assertEqual(response_with_perm.status_code, 200)

    def test_EssayQuestion(self):
        quiz3 = Quiz.objects.create(
            id=3,
            title="test quiz 3",
            description="d3",
            url="tq3",
            category=self.c1,
            exam_paper=True,
        )
        essay = EssayQuestion.objects.create(id=4, content="tell all")
        essay.quiz.add(quiz3)
        self.client.login(email="jacob@jacob.com", password="top_secret")

        response = self.client.post("/tq3/take/")
        self.assertContains(response, "<textarea")

        response = self.client.post(
            "/tq3/take/", {"answers": "The meaning of life is...", "question_id": 4}
        )
        self.assertContains(response, "result")

    def test_user_progress(self):
        response = self.client.get("/tq1/take/")
        self.assertEqual(response.context["progress"], (0, 2))
        response = self.client.post(
            "/tq1/take/",
            {"answers": "123", "question_id": self.client.session["1_q_list"][0]},
        )
        self.assertEqual(response.context["progress"], (1, 2))


class TestTemplateTags(TestCase):
    def setUp(self):
        self.question1 = MCQuestion.objects.create(id=1, content="squawk")

        self.answer1 = Answer.objects.create(
            id=123, question=self.question1, content="bing", correct=False
        )

        self.answer2 = Answer.objects.create(
            id=456, question=self.question1, content="bong", correct=True
        )

        self.question2 = TFQuestion.objects.create(id=3, content="oink", correct=True)
        self.quiz1 = Quiz.objects.create(
            id=1, title="test quiz 1", description="d1", url="tq1"
        )

        self.question1.quiz.add(self.quiz1)
        self.question2.quiz.add(self.quiz1)

        self.user = User.objects.create_user(
            email="jacob@jacob.com", password="top_secret"
        )

        self.sitting = Sitting.objects.new_sitting(self.user, self.quiz1)
        self.sitting.current_score = 1

    def test_correct_answer_all_user(self):
        template = Template(
            "{% load quiz_tags %}" + "{% correct_answer_for_all question %}"
        )

        context = Context({"question": self.question1, "incorrect_questions": [1]})

        self.assertTemplateUsed("correct_answer.html")
        self.assertIn("bing", template.render(context))
        self.assertIn("incorrectly", template.render(context))

    def test_answer_to_string(self):
        template = Template(
            "{% load quiz_tags %}" + "{{ question|answer_choice_to_string:answer }}"
        )

        context = Context(
            {
                "question": self.question1,
                "answer": self.answer1.id,
                "incorrect_questions": [1],
            }
        )

        self.assertIn("bing", template.render(context))
