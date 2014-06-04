from django.contrib import messages
from django.contrib.admin.models import LogEntry, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

from openipam.hosts.models import Host
from openipam.hosts.forms import HostOwnerForm, HostRenewForm


def assign_owner_hosts(request, selected_hosts):
    user = request.user

    # User must have global change permission on hosts to use this action.
    if not user.has_perm('hosts.change_host'):
        messages.error(request, "You do not have permissions to change ownership on the selected hosts. "
                       "Please contact an IPAM administrator.")
    else:
        owner_form = HostOwnerForm(request.POST)

        if owner_form.is_valid():
            user_owners = owner_form.cleaned_data['user_owners']
            group_owners = owner_form.cleaned_data['group_owners']

            for host in selected_hosts:
                # Delete user and group permissions first
                host.remove_owners()

                # Re-assign users
                for user_onwer in user_owners:
                    host.assign_owner(user_onwer)

                # Re-assign groups
                for group_owner in group_owners:
                    host.assign_owner(group_owner)

            messages.success(request, "Ownership for selected hosts has been updated.")

        else:
            error_list = []
            for key, errors in owner_form.errors.items():
                for error in errors:
                    error_list.append(error)
            messages.error(request, mark_safe("There was an error updating the ownership of the selected hosts. "
                    "<br/>%s" % '<br />'.join(error_list)))


def delete_hosts(request, selected_hosts):
    user = request.user

    # Must have global delete perm or object owner perm
    if not user.has_perm('hosts.delete_host') and not change_perms_check(user, selected_hosts):
        messages.error(request, "You do not have permissions to perform this action on one or more the selected hosts. "
                       "Please contact an IPAM administrator.")
    else:
        # Log Deletion
        for host in selected_hosts:
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(host).pk,
                object_id=host.pk,
                object_repr=force_unicode(host),
                action_flag=DELETION
            )

        # Delete hosts
        selected_hosts.delete()

        messages.success(request, "Seleted hosts have been deleted.")


def renew_hosts(request, selected_hosts):
    user = request.user

    # Must have global delete perm or object owner perm
    if not user.has_perm('hosts.change_host') and not change_perms_check(user, selected_hosts):
        messages.error(request, "You do not have permissions to perform this action one or more of the selected hosts. "
                       "Please contact an IPAM administrator.")
    else:
        renew_form = HostRenewForm(user=request.user, data=request.POST)

        if renew_form.is_valid():
            expiration = renew_form.cleaned_data['expire_days'].expiration
            for host in selected_hosts:
                #assert False, host.expires
                host.set_expiration(expiration)
                host.save()

                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(host).pk,
                    object_id=host.pk,
                    object_repr=force_unicode(host),
                    action_flag=CHANGE,
                    change_message='Renewed expiration to %s' % expiration
                )

            messages.success(request, "Expiration for selected hosts have been updated.")

        else:
            error_list = []
            for key, errors in renew_form.errors.items():
                for error in errors:
                    error_list.append(error)
            messages.error(request, mark_safe("There was an error renewing the expiration of the selected hosts. "
                    "<br/>%s" % '<br />'.join(error_list)))


def change_perms_check(user, selected_hosts):
    # Check onwership of hosts for users with only object level permissions.
    user_perms_check = False
    if user.host_change_perms is True:
        user_perms_check = True
    else:
        user_perm_list = [True if host.mac in user.host_change_perms else False for host in selected_hosts]
    if set(user_perm_list) == set([True]):
        user_perms_check = True

    return user_perms_check