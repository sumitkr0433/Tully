# -*- coding: UTF-8 -*-
from django.db import models
from django.contrib.auth.models import User
from easy_thumbnails.fields import ThumbnailerImageField
from taggit.managers import TaggableManager
from userena.utils import generate_sha1
from datetime import datetime
from ebook import settings as ebook_settings
from django.utils.translation import ugettext_lazy as _
from userena.utils import get_gravatar, generate_sha1, get_protocol, \
    get_datetime_now, get_user_model, user_model_label
from dynamic_scraper.models import Scraper, SchedulerRuntime
from scrapy.contrib.djangoitem import DjangoItem
from django.dispatch import receiver
from django.db.models.signals import pre_save,pre_delete




    

STATUS_CHOICES = (('draft', u'草稿'), 
    ('pub', u'发布'),
    ('del', u'删除')
)


SHARED_CHOICES = (
    (1,'分享'),
    (2,'隐私'),
)




def upload_to_thumbnail(instance, filename):
    """
    103,143
    Uploads a thumbnail for a user to the ``EBOOK_THUMBNAIL_PATH`` and saving it
    under unique hash for the image. This is for privacy reasons so others
    can't just browse through the mugshot directory.

    """
    #extension = filename.split('.')[-1].lower()
    extension = 'jpg_103'  
    salt, hash = generate_sha1(instance.id)
    path = ebook_settings.EBOOK_THUMBNAIL_PATH % {'username': instance.created_by.username,
                                                    'id': instance.created_by.id,
                                                    'date': instance.created_by.date_joined,
                                                    'date_now': get_datetime_now().date()}
    return 'thumbnail/products/%(path)s_%(hash)s.%(extension)s' % {'path': path,
                                               'hash': hash[:10],
                                               'extension': extension}





class ProductWebsite(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField()
    scraper = models.ForeignKey(Scraper, blank=True, null=True, on_delete=models.SET_NULL)
    scraper_runtime = models.ForeignKey(SchedulerRuntime, blank=True, null=True, on_delete=models.SET_NULL)

    def __unicode__(self):
        return self.name

class ProductManager(models.Manager):
    def get_all_products(self):
        return Product.objects.filter(status='pub')
    def get_hot_products(self):
        return self.get_all_products().order_by('-num_views')
    def get_last_products(self):
        return self.get_all_products().order_by('-updated_on')
    def get_random_products(self):
        return self.get_all_products().order_by('-rec_on')
    def get_recommend_products(self):
        return self.get_all_products().order_by('?')
    def get_tag_products(self,tag_name):
        return self.get_all_products().filter(tags__name__in=[tag_name]).order_by('-updated_on')


class Product(models.Model):
    '''
    the core Model of Ebook, the buyer and seller can get the 
    list , thumbnail store the Product thumbnail image .
    you can setting the thumbnail size in Settings File through 
    EBOOK_THUMBNAIL_SIZE,EBOOK_THUMBNAIL_PATH,EBOOK_THUMBNAIL_CROP_TYPE
    ForeignKey: User - Created_by
    ForeignKey: Tags  - Tag 
    '''
    title           = models.CharField(max_length=255, blank=False)
    status          = models.CharField(u"发布状态", max_length=16, default='draft', choices=STATUS_CHOICES)
    description     = models.CharField(max_length=255, blank=True, help_text="Because some things want it")
    price           = models.DecimalField(max_digits=8,decimal_places=2)
    #js              = models.TextField(help_text=js_help, blank=True)
    shared          = models.IntegerField(choices=SHARED_CHOICES,default=1)

    '''
    THUMBNAIL_SETTINGS = {'size':(ebook_settings.EBOOK_THUMBNAIL_SIZE,
                                  ebook_settings.EBOOK_THUMBNAIL_SIZE),
                          'crop':ebook_settings.EBOOK_THUMBNAIL_CROP_TYPE}
    '''
    thumbnail = ThumbnailerImageField(_('thumbnail'),
                                    blank=True,
                                    upload_to=upload_to_thumbnail,
                                    #resize_source=THUMBNAIL_SETTINGS,
                                    help_text=_('A book image displayed in the list.'))

    tags = TaggableManager(blank=True)
    created_by = models.ForeignKey(User)


    rec = models.BooleanField(u'推荐', default=False)
    rec_on = models.DateTimeField(blank=True, null=True)
    num_views = models.IntegerField(u'浏览次数', default=0)
    num_replies = models.PositiveSmallIntegerField(u'回复数', default=0)

    num_favorites = models.IntegerField(u'收藏数',default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    focus_date = models.CharField(u'初始日期',max_length=30, null=True, blank=True)
    serialname = models.CharField(u'系列书名',max_length=128)
    serialno   = models.CharField(u'书　　号',max_length=128)
    publish_on = models.DateTimeField(u'出版日期') 
    num_page   = models.CharField(u'页　　数',max_length=8)
    price      = models.FloatField(u'定　　价')
    publish_type = models.CharField(u'印刷方式',max_length=8)
    about = models.TextField(blank=False)
    content = models.TextField()
    origin_name = models.CharField(u'原书书名',max_length=128)
    origin_serial=models.CharField(u'原书书号',max_length=12)
    origin_country=models.CharField(u'原书国家',max_length=16)
    origin_publish=models.CharField(u'原书出版社',max_length=32)
    origin_num = models.CharField('原书页数',max_length=32)
    author = models.CharField('作者',max_length=512)
    objects = ProductManager()

    '''
    update the Product models last update time.
    :param commit,default set True
    '''
    def update_updated_on(self, commit=True):
        self.updated_on = datetime.now()
        if commit:
            self.save()


    '''
    update the Comment count.
    :param commit,default set True
    '''
    def update_num_replies(self, commit=True):
        self.num_replies = self.comment_set.count()
        if commit:
    
            self.save()


    '''
    get the thumbnail image url
    '''
    def get_thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        return getattr(ebook_settings, 'TL_COVER_URL', None)

    '''
    get model Product url
    '''
    @models.permalink
    def get_absolute_url(self):
        return ('product_detail', (self.pk, ))

class ArticleManager(models.Manager):
    def get_all_articles(self):
        return Article.objects.filter(status='pub')
    def get_tag_articles(self):
        return self.get_all_articles().filter(tags__name__in=[tag_name]).order_by('-updated_on')
   

class Article(models.Model):
    article_website = models.ForeignKey(ProductWebsite)
    url             = models.URLField()
    checker_runtime = models.ForeignKey(SchedulerRuntime, blank=True, null=True, on_delete=models.SET_NULL)
    title           = models.CharField(max_length=255, blank=False)
    status          = models.CharField(u"发布状态", max_length=16, default='draft', choices=STATUS_CHOICES)
    description     = models.CharField(max_length=255, blank=True, help_text="Please write some_things")
    shared          = models.IntegerField(choices=SHARED_CHOICES,default=1)
    content         = models.TextField(null=True,blank=True)
    
    '''
    THUMBNAIL_SETTINGS = {'size':(ebook_settings.EBOOK_THUMBNAIL_SIZE,
                                  ebook_settings.EBOOK_THUMBNAIL_SIZE),
                          'crop':ebook_settings.EBOOK_THUMBNAIL_CROP_TYPE}
    '''

    tags = TaggableManager(blank=True)
    created_by = models.ForeignKey(User)
    test = models.TextField(null=True,blank=True)

    rec = models.BooleanField(u'推荐', default=False)
    rec_on = models.DateTimeField(blank=True, null=True)
    num_views = models.IntegerField(u'浏览次数', default=0)
    num_replies = models.PositiveSmallIntegerField(u'回复数', default=0)

    num_favorites = models.IntegerField(u'收藏数',default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    focus_date = models.CharField(u'初始日期', max_length=30, null=True, blank=True)
    #objects = ArticleManager()   
    '''
    update the Product models last update time.
    :param commit,default set True
    '''
    def update_updated_on(self, commit=True):
        self.updated_on = datetime.now()
        if commit:
            self.save()


    '''
    update the Comment count.
    :param commit,default set True
    '''
    def update_num_replies(self, commit=True):
        self.num_replies = self.comment_set.count()
        if commit:
    
            self.save()
    
    def __unicode__(self):
        return self.title

class ArticleItem(DjangoItem):
    django_model = Article


@receiver(pre_delete)
def pre_delete_handler(sender, instance, using, **kwargs):
    if isinstance(instance, Article):
        if instance.checker_runtime:
            instance.checker_runtime.delete()

pre_delete.connect(pre_delete_handler)


class PdComment(models.Model):
    product = models.ForeignKey(Product)
    content = models.TextField()

    created_by = models.ForeignKey(User)
    created_on = models.DateTimeField(u'创建日期', auto_now_add=True)

    def __unicode__(self):
        return "%s-%s" % (self.product.title, self.content[:20])
