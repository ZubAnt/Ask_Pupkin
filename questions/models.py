from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import Http404


class QuestionsManager(models.Manager):
    def get_by_id(self, q_id):
        try:
            return self.get(pk=q_id)
        except Questions.DoesNotExist:
            raise Http404('Question not found')

    def get_new_questions(self):
        q_list = self.order_by('-pub_date')
        return q_list
        # return Questions.objects.fill_questions(q_list)

    def get_best_questions(self):
        q_list = self.order_by('-rating')[:100]
        return Questions.objects.fill_questions(q_list)

    def get_answers_by_id(self, q_id):
        return AnswersManager.get_answers_for_question_by_id(Answers.objects, q_id)

    def get_tags_by_id(self, q_id):
        return self.filter(id=q_id)

    def get_questions_by_tag(self, tag):
        return self.filter(tags=tag).order_by('-pub_date')

    def fill_questions(self, q_list):
        for q in q_list:
            q.tag_list = self.get_tags_by_id(q.id)
            q.answers_count = self.get_count_of_answers(q.id)
        return q_list


class AnswersManager(models.Manager):
    def str_to_bool(self, s):
        if s == 'true':
            return True
        elif s == 'false':
            return False
        else:
            raise ValueError

    def get_count_of_answers_for_question(self, q_id):
        return self.filter(question=q_id).count()

    def get_answers_by_question_id(self, q_id):
        return self.filter(question=q_id).order_by('-pub_date')[:100]

    def get_answer_by_id(self, id):
        return self.get(id=id)

    def set_correct(self, value, answer_id):
        a = Answers.objects.get(pk=answer_id)
        a.correct = self.str_to_bool(value)
        a.save()


class TagsManager(models.Manager):
    def get_tags_for_question_by_id(self, q_id):
        return self.filter(question=q_id)

    def get_popular_tags(self):
        return self.annotate(Count('questions')).order_by('-questions__count')[:10]

    def get_tag_by_name(self, tag_name):
        return self.get(name=tag_name)


class ProfileManager(models.Manager):
    def get_profile_by_user_id(self, user_id):
        return self.get(user=user_id)

    def check_user_unicue(self, login):
        return User.objects.filter(username=login).exists()

    def get_profile_by_user(self, user_id):
        return self.get(user=user_id)


class LikeManager(models.Manager):
    def str_to_bool(self, s):
        if s == 'True':
            return True
        elif s == 'False':
            return False
        else:
            raise ValueError

    def check_a_like(self, user_id, answer_id):
        try:
            ct = ContentType.objects.get(app_label="ask", model="answers")
            check = self.get(user=user_id, content_type=ct, object_id=answer_id).like
        except Like.DoesNotExist:
            check = None
        return check

    def check_q_like(self, user_id, question_id):
        try:
            ct = ContentType.objects.get(app_label="ask", model="questions")
            check = self.get(user=user_id, content_type=ct, object_id=question_id).like
        except Like.DoesNotExist:
            check = None
        return check

    def a_like(self, user_id, answer_id, like0):
        like = self.str_to_bool(like0)
        answer = Answers.objects.get_answer_by_id(answer_id)
        rating = answer.rating

        check = self.check_a_like(user_id, answer_id)
        if check is None:
            ct = ContentType.objects.get(app_label="ask", model="answers")
            l = Like.objects.create(user=user_id, like=like, content_type=ct, object_id=answer_id)
            l.save()
            if like:
                rating += 1
            else:
                rating -= 1
            answer.rating = rating
            answer.save()
            return 'Success', rating
        else:
            if check == like:
                return 'Already', rating
            else:
                ct = ContentType.objects.get(app_label="ask", model="answers")
                l = self.get(user=user_id, content_type=ct, object_id=answer_id)
                l.like = like
                l.save()

                if like == True:
                    rating += 2
                else:
                    rating -= 2
                answer.rating = rating
                answer.save()

                return 'Success', rating

    def q_like(self, user_id, question_id, like0):
        like = self.str_to_bool(like0)
        question = Questions.objects.get_question_by_id(question_id)
        rating = question.rating

        check = self.check_q_like(user_id, question_id)
        if check is None:
            ct = ContentType.objects.get(app_label="ask", model="questions")
            l = Like.objects.create(user=user_id, like=like, content_type=ct, object_id=question_id)
            l.save()
            if like:
                rating += 1
            else:
                rating -= 1
            question.rating = rating
            question.save()
            return 'Success', rating
        else:
            if check == like:
                return 'Already', rating
            else:
                ct = ContentType.objects.get(app_label="ask", model="questions")
                l = self.get(user=user_id, content_type=ct, object_id=question_id)
                l.like = like
                l.save()

                if like:
                    rating += 2
                else:
                    rating -= 2
                question.rating = rating
                question.save()

                return 'Success', rating


# ______________MODELS______________#


class Questions(models.Model):
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    text = models.TextField()
    rating = models.IntegerField(default=0)
    pub_date = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0)
    tags = models.ManyToManyField('Tags')

    objects = QuestionsManager()

    def get_count_of_answers(self):
        return self.answers_set.count()

    def get_all_tags(self):
        return self.tags.all()

    class Meta:
        db_table = 'Questions'


class Answers(models.Model):
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    question = models.ForeignKey('Questions', on_delete=models.CASCADE)
    text = models.TextField()
    rating = models.IntegerField(default=0)
    pub_date = models.DateTimeField(auto_now_add=True)

    objects = AnswersManager()

    class Meta:
        db_table = 'Answers'


class Tags(models.Model):
    name = models.CharField(max_length=255)
    objects = TagsManager()

    class Meta:
        db_table = 'Tags'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    objects = ProfileManager()

    class Meta:
        db_table = 'Profile'


class Like(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    user = models.ForeignKey('Profile')
    like = models.BooleanField()
    objects = LikeManager()

    class Meta:
        db_table = 'Like'
