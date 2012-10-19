import re

from taxi.utils import terminal
from taxi.exceptions import CancelException
from taxi.models import Project

class BaseUi(object):
    def msg(self, message):
        print(message)

    def err(self, message):
        self.msg(u"Error: %s" % message)

    def projects_list(self, projects, numbered=False):
        for (key, project) in enumerate(projects):
            if numbered:
                self.msg(u"(%d) %-4s %s" % (key, project.id, project.name))
            else:
                self.msg(u"%-4s %s" % (key, project.id, project.name))

    def project_with_activities(self, project, numbered_activities=False):
        self.msg(project)
        self.msg(u"\nActivities:")
        for (key, activity) in enumerate(project.activities):
            self.msg(u"(%d) %-4s %s" % (key, activity.id, activity.name))

    def select_project(self, projects):
        try:
            return terminal.select_number(len(projects), u"Choose the project "
                                          "(0-%d), (Ctrl-C) to exit: " %
                                          (len(projects) - 1))
        except KeyboardError:
            raise CancelException()

    def select_activity(self, activities):
        try:
            return terminal.select_number(len(activities), u"Choose the "
                                          "activity (0-%d), (Ctrl-C) to exit: " %
                                          (len(project.activities) - 1))
        except KeyboardError:
            raise CancelException()

    def select_alias(self):
        try:
            return terminal.select_string(u"Enter the alias for .tksrc (a-z, - "
                                          "and _ allowed), (Ctrl-C) to exit: ",
                                          r'^[\w-]+$')
        except KeyboardError:
            raise CancelException()

    def overwrite_alias(self, alias, mapping, retry=True):
        mapping_name = Project.tuple_to_str(mapping)

        if retry:
            choices = 'y/n/R(etry)'
            default_choice = 'r'
            choice_regexp = r'^[ynr]$'
        else:
            choices = 'y/N'
            default_choice = 'n'
            choice_regexp = r'^[yn]$'

        s = (u"The alias `%s` is already mapped to `%s`.\nDo you want to "
             "overwrite it [%s]? " % (alias, mapping_name, choices))

        overwrite = terminal.select_string(s, choice_regexp, re.I, default_choice)

        if overwrite == 'n':
            return False
        elif overwrite == 'y':
            return True

        return None

    def alias_added(self, alias, mapping):
        mapping_name = Project.tuple_to_str(mapping)

        self.msg(u"The following alias has been added to your configuration "
                 "file: %s = %s" % ((alias) + mapping_name))

    def _show_mapping(self, mapping, project, alias_first=True):
        (alias, t) = mapping

        mapping_name = '%s/%s' % t

        if not project:
            project_name = '?'
        else:
            if t[1] is None:
                project_name = project.name
                mapping_name = t[0]
            else:
                activity = project.get_activity(t[1])

                if activity is None:
                    project_name = u'%s, ?' % (project.name)
                else:
                    project_name = u'%s, %s' % (project.name, activity.name)

        if alias_first:
            args = (alias, mapping_name, project_name)
        else:
            args = (mapping_name, alias, project_name)

        self.msg(u"%s -> %s (%s)" % args)

    def mapping_detail(self, mapping, project):
        self._show_mapping(mapping, project, False)

    def alias_detail(self, mapping, project):
        self._show_mapping(mapping, project, True)

    def clean_inactive_aliases(self, aliases):
        self.msg(u"The following aliases are mapped to inactive projects:\n")

        for (mapping, project) in aliases:
            self.alias_detail(mapping, project)

        confirm = terminal.select_string(u"\nDo you want to clean them [y/N]? ",
                                         r'^[yn]$', re.I, 'n')

        return confirm == 'y'

    def pushed_hours_total(self, pushed_hours, ignored_hours):
        self.msg(u'\n%-29s %5.2f' % ('Total', pushed_hours))

        if ignored_hours > 0:
            self.msg(u'%-29s %5.2f' % ('Total ignored', ignored_hours))

    def non_working_dates_commit_error(self, dates):
        dates = [d.strftime('%A %d %B') for d in dates]

        self.err(u"You're trying to commit for a day that's "
        " on a week-end or that's not yesterday nor today (%s).\n"
        "To ignore this error, re-run taxi with the option "
        "`--ignore-date-error`" % ', '.join(dates))

    def show_status(self, entries_list):
        self.msg(u'Staging changes :\n')
        entries_list = sorted(entries_list)

        for (date, entries) in entries_list:
            if len(entries) == 0:
                continue

            subtotal_hours = 0
            self.msg(u'# %s #' % date.strftime('%A %d %B').capitalize())
            for entry in entries:
                self.msg(entry)
                subtotal_hours += entry.get_duration() or 0

            self.msg(u'%-29s %5.2f\n' % ('', subtotal_hours))
            total_hours += subtotal_hours

        self.pushed_hours_total(total_hours, 0)
        self.msg(u'\nUse `taxi ci` to commit staging changes to the server')