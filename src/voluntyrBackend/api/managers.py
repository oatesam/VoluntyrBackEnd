from django.contrib.auth.models import BaseUserManager


class EndUserManager(BaseUserManager):
    def create_user(self, email, password, authy_id):
        """
        Creates and saves an EndUser with the given email and password.
        :param email: This EndUser's email
        :param password: This EndUser's password
        :return: Saved EndUser model object
        """
        if not email:
            raise ValueError('EndUser must have an email address')
        if not password:
            raise ValueError('EndUser must have a password')
        if not authy_id:
            raise ValueError('EndUser must have an authy_id')

        user = self.model(email=email, authy_id=authy_id)

        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, authy_id):
        """
        Creates and saves a super EndUser with the given email and password.
        :param email: This EndUser's email
        :param password: This EndUser's password
        :return: Saved EndUser model object
        """
        if not email:
            raise ValueError('EndUser must have an email address')
        if not password:
            raise ValueError('EndUser must have a password')
        if not authy_id:
            raise ValueError('EndUser must have an authy_id')

        user = self.model(email=email, authy_id=authy_id, is_admin=True, is_staff=True, is_superuser=True)

        user.set_password(password)
        user.save()
        return user
