"""
There are two key models in the Consent app. These are `Privilege` and
`Consent`. A `Privilege` is created for the website/app and then someone (or
something) has the option of granting its consent to the use of that
`Privilege`. After the `Consent` has been granted, it can also be revoked.
"""
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class Privilege(models.Model):
    """
    A privilege is a permission that the project asks for from something.

    For example, `Prilivege`s could be the permission to send newsletters to
    a subscriber or the permission to share a user's details.
    """
    name = models.CharField(max_length=64)
    description = models.TextField()

    class Meta:
        default_related_name = 'privileges'
        ordering = ['name', ]
        verbose_name = _('privilege')
        verbose_name_plural = _('privileges')

    def __str__(self):
        return self.name

    def is_granted_by(self, user):
        consent = Consent.objects.get_or_none(user=user, privilege=self)
        if consent:
            return consent.is_granted
        return False


class ConsentManager(models.Manager):
    """
    The ConsentManager adds a number of utility methods to the Consent.objects
    interface to help with common tasks and functions.
    """

    def _get_content_type_params(obj):
        return {
            'content_type': ContentType.objects.get_for_model(obj),
            'object_id': obj.id
        }

    def for_object(self, obj):
        """
        Return the Consent instances for a given object.
        """
        kwargs = self._get_content_type_params(obj)
        return Consent.objects.filter(**kwargs)

    def for_user(self, user):
        """
        Return the Consent instances for a given user.

        This exists for backwards compatibility only.
        """
        return self.for_object(user)

    def grant_consent(self, obj, privileges):
        """
        Grant an QuerySet (or iterable) of privileges for a specific object.
        """
        kwargs = self._get_content_type_params(obj)
        for privilege in privileges:
            consent, created = Consent.objects  \
                .get_or_create(privilege=privilege, **kwargs)
            if not created:
                consent.revoked = False
                consent.revoked_on = None
                consent.save()

    def revoke_consent(self, obj, privileges):
        """
        Revoke an QuerySet (or iterable) of privileges for a specific object.
        """
        ctype = ContentType.objects.get_for_model(obj)
        Consent.objects  \
            .filter(content_type=ctype,
                    object_id=obj.id,
                    privilege__in=privileges)  \
            .update(revoked=True,
                    revoked_on=timezone.now())

    def granted(self, obj=None):
        """
        Return all of the granted consents for all objects or the given one.
        """
        granted_consents = self.filter(revoked=False)
        if obj:
            kwargs = self._get_content_type_params(obj)
            granted_consents = granted_consents.filter(**kwargs)
        return granted_consents

    def revoked(self, obj=None):
        """
        Return all of the revoked consents for all objects or the given one.
        """
        revoked_consents = self.filter(revoked=True)
        if obj:
            kwargs = self._get_content_type_params(obj)
            revoked_consents = revoked_consents.filter(**kwargs)
        return revoked_consents

    def get_or_none(self, *args, **kwargs):

        try:
            return self.get(*args, **kwargs)
        except Consent.DoesNotExist:
            pass

        return None


class Consent(models.Model):
    """
    Consent is the grant or forbiddance of a specific `Privilege`.
    Usually, the one granting consent is a user, however this is not
    enforced and anything (ie any `Model`) can grant `Consent`, via a
    `generic relation`_.

    .. _generic relation: https://docs.djangoproject.com/en/stable/ref/contrib/contenttypes/#generic-relations
    """  # NOQA
    granter_ctype = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    granter_id = models.PositiveIntegerField()
    granter = GenericForeignKey('granter_ctype', 'granter_id')

    privilege = models.ForeignKey(Privilege, on_delete=models.CASCADE)

    granted_on = models.DateTimeField(default=timezone.now)
    revoked_on = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)

    notes = models.TextField(blank=True, help_text=_(
        'You can use this to keep notes of how the consent was granted, '
        'such as the actual text that was used to ask for consent.'))

    objects = ConsentManager()

    class Meta:
        unique_together = ('granter_ctype', 'granter_id', 'privilege')
        default_related_name = 'consents'
        ordering = ['privilege__name', ]
        verbose_name = _('consent')
        verbose_name_plural = _('consents')

    def revoke(self):
        """
        Revoke this object's `Consent` for this `Privilege`.
        """
        if not self.revoked:
            self.revoked = True
            self.revoked_on = timezone.now()

    def grant(self):
        """
        Grant the Consent for this `Privilege` as granted.
        """
        if self.revoked:
            self.revoked = False
            self.revoked_on = None
            self.granted_on = timezone.now()

    @property
    def is_granted(self):
        """
        Return True if this consent has not been revoked or False otherwise.
        """
        return not self.revoked

    @property
    def is_revoked(self):
        """
        Return `True` if this consent has been revoked or `False` otherwise.
        """
        return not self.is_granted

    def __str__(self):

        if not self.revoked:
            adjv = 'permits'
        else:
            adjv = 'revoked'

        return "{} {} the '{}' privilege".format(
            self.granter, adjv, self.privilege
        )
