# -*- coding: utf-8 -*-
from odoo import api, models


class ReportPosLiteSessionCloseSummary(models.AbstractModel):
    _name = 'report.pos_lite.report_session_close_summary_document'
    _description = 'POS Lite Session Close Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['pos.lite.session'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'pos.lite.session',
            'docs': docs,
            'data': data or {},
            'get_summary': lambda session: session._get_close_summary(),
        }
