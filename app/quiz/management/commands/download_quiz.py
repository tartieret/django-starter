from django.core.management.base import BaseCommand, CommandError

from rest_framework.renderers import JSONRenderer

from app.quiz.models import Quiz
from app.quiz.serializers import QuizSerializer


class Command(BaseCommand):
    help = "Export a quiz to JSON"

    def add_arguments(self, parser):
        parser.add_argument("id", nargs="?", type=int)
        parser.add_argument(
            "--filepath", "-f", nargs="?", type=str, default="quiz.json"
        )

    def handle(self, *args, **options):
        quiz_id = options["id"]
        filepath = options["filepath"]
        try:
            quiz = Quiz.objects.get(pk=quiz_id)
            serializer = QuizSerializer(quiz)
            json = JSONRenderer().render(serializer.data)
            with open(filepath, "w") as file:
                file.write(json.decode())
            self.stdout.write(
                self.style.SUCCESS("Downloaded quiz %d to %s" % (quiz_id, filepath))
            )
        except Quiz.DoesNotExist:
            raise CommandError('Quiz "%s" does not exist' % quiz_id)
