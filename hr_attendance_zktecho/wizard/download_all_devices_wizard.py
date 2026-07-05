# -*- coding: utf-8 -*-

import logging
import threading
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger('biometric_device')


class DownloadAllDevicesWizard(models.TransientModel):
    _name = 'download.all.devices.wizard'
    _description = 'Download Attendance From All Devices'

    date_from = fields.Datetime('From', required=True)
    date_to = fields.Datetime('To', required=True)

    def action_download(self):
        """Trigger attendance download from ALL devices in a background thread.

        Returns immediately with a notification so the browser doesn't
        time-out waiting for the long-running device sync to finish.
        """
        self.ensure_one()
        machines = self.env['biomteric.device.info'].search([])
        if not machines:
            raise UserError(_('No biometric devices configured.'))

        # Capture IDs and context for the background thread
        machine_ids = machines.ids
        date_from = self.date_from
        date_to = self.date_to
        db_name = self.env.cr.dbname
        uid = self.env.uid
        context = dict(self.env.context)

        def _download_in_background():
            """Run in a separate thread with its own cursor."""
            import odoo
            with odoo.registry(db_name).cursor() as new_cr:
                new_env = api.Environment(new_cr, uid, context)
                devices = new_env['biomteric.device.info'].browse(machine_ids)
                errors = []
                success_count = 0
                for machine in devices:
                    # Save original date range values
                    orig_from = machine.sync_date_from
                    orig_to = machine.sync_date_to
                    try:
                        # Temporarily set the wizard's date range on the device
                        machine.write({
                            'sync_date_from': date_from,
                            'sync_date_to': date_to,
                        })
                        machine.download_attendance_oldapi()
                        success_count += 1
                        # Commit after each successful device download
                        new_cr.commit()
                    except Exception as e:
                        new_cr.rollback()
                        errors.append("%s (%s): %s" % (machine.name, machine.ipaddress, str(e)))
                        _logger.error('Failed to download from device %s: %s', machine.name, str(e))
                    finally:
                        try:
                            machine.write({
                                'sync_date_from': orig_from,
                                'sync_date_to': orig_to,
                            })
                            new_cr.commit()
                        except Exception:
                            new_cr.rollback()

                if errors:
                    _logger.error('Download completed with errors:\n%s', '\n'.join(errors))
                else:
                    _logger.info('Download completed successfully from %d device(s).', success_count)

        # Launch background thread
        thread = threading.Thread(target=_download_in_background, daemon=True)
        thread.start()
        _logger.info('Attendance download started in background thread for %d device(s).', len(machine_ids))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Download Started'),
                'message': _('Attendance download started in the background for %d device(s). '
                             'You can continue working — check the logs for progress.') % len(machine_ids),
                'type': 'info',
                'sticky': True,
            }
        }
