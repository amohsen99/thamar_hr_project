# -*- coding: utf-8 -*-
"""Fix singleton crash in hr_work_entry_attendance _get_attendance_intervals.

The enterprise module ``hr_work_entry_attendance`` accesses
``overtime.status`` on a potentially multi-record recordset (line 94
of hr_version.py), which triggers ``ensure_one()`` and crashes:

    ValueError: Expected singleton: hr.attendance.overtime.line(…)

This override replaces the buggy overtime-filtering loop with one
that safely iterates over each record in the (possibly stacked)
recordset.
"""
import logging
from collections import defaultdict
from datetime import timedelta

from pytz import timezone
from odoo import models
from odoo.tools.intervals import Intervals

_logger = logging.getLogger(__name__)


class HrVersion(models.Model):
    _inherit = 'hr.version'

    def _get_attendance_intervals(self, start_dt, end_dt):
        """Patched version that handles multi-record overtime recordsets.

        Replicates the logic from ``hr_work_entry_attendance`` but fixes
        the singleton assumption when checking ``overtime.status``.
        """
        ##################################
        #   ATTENDANCE BASED CONTRACTS   #
        ##################################
        start_naive = start_dt.replace(tzinfo=None)
        end_naive = end_dt.replace(tzinfo=None)
        attendance_based_contracts = self.filtered(
            lambda c: c.work_entry_source == 'attendance')
        search_domain = [
            ('employee_id', 'in', attendance_based_contracts.employee_id.ids),
            ('check_in', '<', end_naive),
            ('check_out', '>', start_naive),
        ]
        resource_ids = attendance_based_contracts.employee_id.resource_id.ids
        attendances = (
            self.env['hr.attendance'].sudo().search(search_domain)
            if attendance_based_contracts
            else self.env['hr.attendance']
        )
        intervals = defaultdict(list)
        for attendance in attendances:
            emp_cal = attendance._get_employee_calendar()
            resource = attendance.employee_id.resource_id
            tz = timezone(emp_cal.tz or resource.tz)
            check_in_tz = attendance.check_in.astimezone(tz)
            check_out_tz = attendance.check_out.astimezone(tz)
            if attendance.overtime_status == 'refused':
                check_out_tz -= timedelta(hours=attendance.validated_overtime_hours)
            if (attendance.employee_id.resource_calendar_id
                    and not attendance.employee_id.resource_calendar_id.flexible_hours):
                lunch_intervals = attendance.employee_id._employee_attendance_intervals(
                    check_in_tz, check_out_tz, lunch=True)
                leaves = (
                    emp_cal._leave_intervals_batch(check_in_tz, check_out_tz, None)[False]
                    if emp_cal
                    else Intervals([], keep_distinct=True)
                )
                real_lunch_intervals = lunch_intervals - leaves
                attendance_intervals = (
                    Intervals([(check_in_tz, check_out_tz, attendance)])
                    - real_lunch_intervals
                )
            else:
                attendance_intervals = Intervals([(check_in_tz, check_out_tz, attendance)])
            for interval in attendance_intervals:
                intervals[attendance.employee_id.resource_id.id].append((
                    max(start_dt, interval[0]),
                    min(end_dt, interval[1]),
                    attendance,
                ))

        mapped_intervals = {
            r: Intervals(intervals[r], keep_distinct=True)
            for r in resource_ids
        }

        # Call the base (calendar-based) _get_attendance_intervals,
        # skipping the enterprise hr_work_entry_attendance override
        # that we are replacing.  We import the enterprise class to
        # call super() on it specifically.
        from odoo.addons.hr_work_entry_attendance.models.hr_version import (
            HrVersion as EnterpriseHrVersion,
        )
        base_result = super(EnterpriseHrVersion, self)._get_attendance_intervals(
            start_dt, end_dt)
        mapped_intervals.update(base_result)

        overtime_intervals = {
            r: Intervals(keep_distinct=True) for r in mapped_intervals
        }
        overtime_contracts = self.filtered(
            lambda c: c.work_entry_source == 'attendance' or c.overtime_from_attendance)
        overtime_intervals.update(
            overtime_contracts._get_overtime_intervals(start_dt, end_dt))

        # ── FIX: handle multi-record overtime recordsets safely ──
        # When Intervals merges overlapping entries the third tuple
        # element can be a multi-record recordset.  The original code
        # called ``overtime.status`` which triggers ensure_one().
        # We iterate over each record instead.
        work_entry_overtime_intervals = defaultdict(list)
        for r, itvs in overtime_intervals.items():
            for start, end, overtime in itvs:
                has_work_entry_type = bool(overtime.rule_ids.work_entry_type_id)
                all_approved = all(
                    ot.status == 'approved' for ot in overtime
                )
                if not (has_work_entry_type and all_approved):
                    continue
                work_entry_overtime_intervals[r].extend([
                    (start, end, overtime)
                ])

        result = {
            r: (mapped_intervals[r] - overtime_intervals[r])
            | Intervals(work_entry_overtime_intervals[r], keep_distinct=True)
            for r in mapped_intervals
        }
        return result
