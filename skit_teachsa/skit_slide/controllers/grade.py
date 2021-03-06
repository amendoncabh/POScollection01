# -*- coding: utf-8 -*-

import json
import base64
import logging
import werkzeug

from odoo import http, _
from odoo.exceptions import AccessError, UserError
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from datetime import date, datetime, timedelta

_logger = logging.getLogger(__name__)


class WebsiteGrade(http.Controller):

    @http.route('/grades-subjects/', type='http', auth='public', website=True, sitemap=False)
    def grade(self, **kw):
        request.session['quiz_answer'] = []
        grades = request.env['product.category'].sudo().search([('is_grade', '=', True)])
        user_id = request.env.uid
        user = request.env['res.users'].sudo().search([('id', '=', user_id)])
        partner = user.partner_id
        channels = []
        breadcrumbs = []
        student = False
        isparent = False
        first_breadcurmb_active = False
        request.session['first_breadcurmb_active'] = False
        valid_subjects = []
        sub_title = 'Grades'
        slide_slide = request.env['slide.slide']
        name = ''
        if(partner.isparent):
            name = partner.name
            isparent = True
        if(partner.isstudent):
            name = partner.name
            student = True
            breadcrumbs.append('Grade')
            student = True
            now = datetime.now()
            cdatetime = now.strftime("%Y-%m-%d")
            current_date = datetime.strptime(cdatetime, '%Y-%m-%d')
            channel_partner = request.env['slide.channel.partner'].sudo().search([
                ('partner_id', '=', user.partner_id.id),
                ('valid_upto', '>=', current_date)])
            for sub in channel_partner:
                valid_subjects.append(sub.channel_id.id)
            if(channel_partner):
                channels = request.env['slide.channel'].sudo().search([
                    ('product_categ_id', '=', channel_partner[0].product_categ_id.id)])
                breadcrumbs.append(channel_partner[0].product_categ_id.name)
                sub_title = channel_partner[0].product_categ_id.name
        values = {'grades': grades,
                  'partner_id': partner.id,
                  'isstudent': student,
                  'name': name,
                  'channels': channels,
                  'breadcrumbs': breadcrumbs,
                  'slide_slide': slide_slide,
                  'valid_subjects': valid_subjects,
                  'isstudent': student,
                  'isparent': isparent,
                  'first_breadcurmb_active': first_breadcurmb_active,
                  'sub_title': sub_title
                  }
        return request.render('skit_slide.website_elearning_grade', values)

    @http.route(['/grades-subjects/content'], type='json', auth="public", methods=['POST'], website=True)
    def grade_subjects(self, **kw):
        channels = []
        breadcrumbs = []
        student = False
        first_breadcurmb_active = False
        request.session['first_breadcurmb_active'] = False
        valid_subjects = []
        slide_slide = request.env['slide.slide']
        user = request.env['res.users'].sudo().search([
            ('id', '=', int(request.env.uid))])

        if(kw.get('categ_id') and (not user.partner_id.isstudent)):
            breadcrumbs.append('Grade')
            prod_categ = request.env['product.category'].sudo().search([
                ('id', '=', kw.get('categ_id'))])
            channels = request.env['slide.channel'].sudo().search([
                ('product_categ_id', '=', prod_categ.id)])
            breadcrumbs.append(prod_categ.name)
            for sub in channels:
                valid_subjects.append(sub.id)
        if(user.partner_id.isstudent):
            breadcrumbs.append('Grade')
            student = True
            now = datetime.now()
            cdatetime = now.strftime("%Y-%m-%d")
            current_date = datetime.strptime(cdatetime, '%Y-%m-%d')
            channel_partner = request.env['slide.channel.partner'].sudo().search([
                ('partner_id', '=', user.partner_id.id),
                ('valid_upto', '>=', current_date)])
            for sub in channel_partner:
                valid_subjects.append(sub.channel_id.id)
            if(channel_partner):
                channels = request.env['slide.channel'].sudo().search([
                    ('product_categ_id', '=', channel_partner[0].product_categ_id.id)])
                breadcrumbs.append(channel_partner[0].product_categ_id.name)
                sub_title = channel_partner[0].product_categ_id.name
        if(kw.get('categ_id')):
            first_breadcurmb_active = True
            request.session['first_breadcurmb_active'] = True
            sub_title = 'Subjects'

        values = {'channels': channels,
                  'breadcrumbs': breadcrumbs,
                  'slide_slide': slide_slide,
                  'valid_subjects': valid_subjects,
                  'isstudent': student,
                  'first_breadcurmb_active': first_breadcurmb_active,
                  'sub_title': sub_title}
        if(kw.get('is_study')):
            return request.env['ir.ui.view'].render_template("skit_slide.website_grade_subjects_details", values)
        return request.env['ir.ui.view'].render_template("skit_slide.website_elearning_grade_subjects", values)

    @http.route(['/grades-subjects/topics'], type='json', auth="public", methods=['POST'], website=True)
    def subject_topics(self, **kw):
        channels = []
        contents = []
        breadcrumbs = []
        first_breadcurmb_active = request.session.get('first_breadcurmb_active')
        breadcrumbs.append('Grade')
        if(kw.get('channel_id')):
            channels = request.env['slide.channel'].sudo().search([
                ('id', '=', kw.get('channel_id'))])
            breadcrumbs.append(channels.product_categ_id.name)
            if channels:
                breadcrumbs.append(channels[0].name)
            if request.env.uid == 4:
                slides = request.env['slide.slide'].sudo().search([
                    ('channel_id', '=', channels.id),
                    ('is_preview', '=', True),
                    ('display_type', '=', 'line_section')], order='sequence')
            else:
                slides = request.env['slide.slide'].sudo().search([
                    ('channel_id', '=', channels.id),
                    ('display_type', '=', 'line_section')], order='sequence')
            i = 1
            slide_size = len(slides)
            for slide in slides:
                slide_content = []
                next_slide = i + 1
                if(next_slide <= slide_size):
                    next_slide_seq = slides[i].sequence
                    if request.env.uid == 4:
                        document_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('is_preview', '=', True),
                            ('sequence', '>', slide.sequence),
                            ('sequence', '<', next_slide_seq),
                            ('slide_type', '=', 'document')])
                    else:
                        document_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('sequence', '>', slide.sequence),
                            ('sequence', '<', next_slide_seq),
                            ('slide_type', '=', 'document')])
                    documents = {}
                    documents['name'] = 'Documents'
                    documents['count'] = len(document_content)
                    documents['slide_type'] = 'document'
                    documents['datas'] = document_content
                    slide_content.append(documents)

                    if request.env.uid == 4:
                        presentation_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('is_preview', '=', True),
                            ('sequence', '>', slide.sequence),
                            ('sequence', '<', next_slide_seq),
                            ('slide_type', '=', 'presentation')])
                    else:
                        presentation_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('sequence', '>', slide.sequence),
                            ('sequence', '<', next_slide_seq),
                            ('slide_type', '=', 'presentation')])
                    documents = {}
                    documents['name'] = 'Presentations'
                    documents['count'] = len(presentation_content)
                    documents['slide_type'] = 'presentation'
                    documents['datas'] = presentation_content
                    slide_content.append(documents)

                    if request.env.uid == 4:
                        video_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('is_preview', '=', True),
                            ('sequence', '>', slide.sequence),
                            ('sequence', '<', next_slide_seq),
                            ('slide_type', '=', 'video')])
                    else:
                        video_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('sequence', '>', slide.sequence),
                            ('sequence', '<', next_slide_seq),
                            ('slide_type', '=', 'video')])
                    documents = {}
                    documents['name'] = 'Videos'
                    documents['count'] = len(video_content)
                    documents['slide_type'] = 'video'
                    documents['datas'] = video_content
                    slide_content.append(documents)

                    if request.env.uid == 4:
                        quiz_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('is_preview', '=', True),
                            ('sequence', '>', slide.sequence),
                            ('sequence', '<', next_slide_seq),
                            ('slide_type', '=', 'quiz')])
                    else:
                        quiz_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('sequence', '>', slide.sequence),
                            ('sequence', '<', next_slide_seq),
                            ('slide_type', '=', 'quiz')])
                    documents = {}
                    documents['name'] = 'Quiz'
                    documents['count'] = len(quiz_content)
                    documents['slide_type'] = 'quiz'
                    documents['datas'] = quiz_content
                    slide_content.append(documents)

                    contents.append({'slide'+str(slide.id): slide_content})
                else:
                    if request.env.uid == 4:
                        document_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('is_preview', '=', True),
                            ('sequence', '>', slide.sequence),
                            ('slide_type', '=', 'document')])
                    else:
                        document_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('sequence', '>', slide.sequence),
                            ('slide_type', '=', 'document')])
                    documents = {}
                    documents['name'] = 'Documents'
                    documents['count'] = len(document_content)
                    documents['slide_type'] = 'document'
                    documents['datas'] = document_content
                    slide_content.append(documents)

                    if request.env.uid == 4:
                        presentation_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('is_preview', '=', True),
                            ('sequence', '>', slide.sequence),
                            ('slide_type', '=', 'presentation')])
                    else:
                        presentation_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('sequence', '>', slide.sequence),
                            ('slide_type', '=', 'presentation')])
                    documents = {}
                    documents['name'] = 'Presentations'
                    documents['count'] = len(presentation_content)
                    documents['slide_type'] = 'presentation'
                    documents['datas'] = presentation_content
                    slide_content.append(documents)

                    if request.env.uid == 4:
                        video_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('is_preview', '=', True),
                            ('sequence', '>', slide.sequence),
                            ('slide_type', '=', 'video')])
                    else:
                        video_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('sequence', '>', slide.sequence),
                            ('slide_type', '=', 'video')])
                    documents = {}
                    documents['name'] = 'Videos'
                    documents['count'] = len(video_content)
                    documents['slide_type'] = 'video'
                    documents['datas'] = video_content
                    slide_content.append(documents)

                    if request.env.uid == 4:
                        quiz_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('is_preview', '=', True),
                            ('sequence', '>', slide.sequence),
                            ('slide_type', '=', 'quiz')])
                    else:
                        quiz_content = request.env['slide.slide'].sudo().search([
                            ('channel_id', '=', channels.id),
                            ('sequence', '>', slide.sequence),
                            ('slide_type', '=', 'quiz')])
                    documents = {}
                    documents['name'] = 'Quiz'
                    documents['count'] = len(quiz_content)
                    documents['slide_type'] = 'quiz'
                    documents['datas'] = quiz_content
                    slide_content.append(documents)

                    contents.append({'slide'+str(slide.id): slide_content})
                i = i + 1
        values = {'topics': slides,
                  'breadcrumbs': breadcrumbs,
                  'contents': contents,
                  'first_breadcurmb_active': first_breadcurmb_active}
        return request.env['ir.ui.view'].render_template("skit_slide.website_grade_subject_topics", values)

    @http.route(['/grades-subjects/topic/detail'], type='json', auth="public", methods=['POST'], website=True)
    def topic_detail(self, **kw):
        slide = []
        breadcrumbs = []
        first_breadcurmb_active = request.session.get('first_breadcurmb_active')
        breadcrumbs.append('Grade')
        if(kw.get('slide_id')):
            slide = request.env['slide.slide'].sudo().search([
                ('id', '=', kw.get('slide_id'))])
            if slide:
                breadcrumbs.append(slide.channel_id.product_categ_id.name)
                breadcrumbs.append(slide.channel_id.name)
                breadcrumbs.append(slide.name)
            """ Create a content subscribed while student login"""
            if request.env.uid != 4:
                now = datetime.now()
                cdatetime = now.strftime("%Y-%m-%d %H:%M:%S")
                current_date = datetime.strptime(cdatetime, '%Y-%m-%d %H:%M:%S')
                student = request.env['res.users'].browse(request.env.uid)
                channel_partner = request.env['slide.channel.partner'].sudo().search([
                    ('partner_id', '=', student.partner_id.id), ('channel_id', '=', slide.channel_id.id)])
                seq_no = len(channel_partner.content_subscribed_ids) + 1
                request.env['slide.content.subscribed'].sudo().create({
                    'seq_no': seq_no,
                    'res_partner_id': student.partner_id.id,
                    'content_id': slide.id,
                    'channel_partner_id': channel_partner.id,
                    'view_datetime': current_date,
                    })
        values = {'slide': slide,
                  'breadcrumbs': breadcrumbs,
                  'first_breadcurmb_active': first_breadcurmb_active
                  }
        return request.env['ir.ui.view'].render_template("skit_slide.topic_slide_detail_view", values)

    @http.route(['/grades-subjects/topic/quiz'], type='json', auth="public", methods=['POST'], website=True)
    def next_question(self, **kw):
        slide_question = []
        checked_value = []
        if(request.session.get('quiz_answer')):
            val = request.session.get('quiz_answer')
            val[kw.get('question_id')] = kw.get('selected_option')
            request.session['quiz_answer'] = val
            next_qest_id = 0
            if(kw.get('type') == 'next'):
                next_qest_id = int(kw.get('question_id')) + 1
            else:
                next_qest_id = int(kw.get('question_id')) - 1
            if(val.get(str(next_qest_id))):
                checked_value = val.get(str(next_qest_id))
        else:
            val = {kw.get('question_id'): kw.get('selected_option')}
            request.session['quiz_answer'] = val

        no = int(kw.get('question_no'))
        if(kw.get('slide_id')):
            slide = request.env['slide.slide'].sudo().search([
                ('id', '=', kw.get('slide_id'))])
            question_no = int(kw.get('question_no'))
            current_ques = question_no - 1
            slide_question = slide.quiz_question_ids[current_ques]

            """ Create a quiz log while student login"""
            if request.env.uid != 4:
                student = request.env['res.users'].browse(request.env.uid)
                content_subscrib = request.env['slide.content.subscribed'].sudo().search([
                    ('res_partner_id', '=', student.partner_id.id)],
                    order='seq_no desc', limit=1)
                if(val.get(kw.get('question_id'))):
                    exit_quiz_log = request.env['quiz.log'].sudo().search([
                        ('question_id', '=', int(kw.get('question_id'))),
                        ('content_subscribed_id', '=', content_subscrib.id)])
                    if not exit_quiz_log:
                        stud_choose = val.get(kw.get('question_id'))
                        status = 'wrong'
                        stud_answer = request.env['slide.answer'].sudo().search([('id', 'in', stud_choose)])
                        answer = request.env['slide.answer'].sudo().search([
                            ('quiz_answer_line_id', '=', int(kw.get('question_id'))),
                            ('is_correct', '=', True)])
                        if(stud_answer.ids == answer.ids):
                            status = 'correct'
                        request.env['quiz.log'].sudo().create({
                            'question_id': int(kw.get('question_id')),
                            'content_subscribed_id': content_subscrib.id,
                            'answer_id': [(6, 0, stud_answer.ids)],
                            'partner_id': student.partner_id.id,
                            'status': status
                            })
        values = {'quiz_question': slide_question,
                  'question_no': no,
                  'checked_value': checked_value
                  }
        return request.env['ir.ui.view'].render_template("skit_slide.document_question", values)

    @http.route(['/grades-subjects/quiz/result'], type='json', auth="public", methods=['POST'], website=True)
    def question_result(self, **kw):
        slide_id = kw.get('slide_id')
        total_question = 0
        correct_answer = 0
        not_attempt = 0
        answer_set = {}
        val = {}
        if(request.session.get('quiz_answer')):
            val = request.session.get('quiz_answer')
            val[kw.get('question_id')] = kw.get('selected_option')
            request.session['quiz_answer'] = val
            answer_set = request.session.get('quiz_answer')
        else:
            val = {kw.get('question_id'): kw.get('selected_option')}
            request.session['quiz_answer'] = val
            answer_set = request.session.get('quiz_answer')
        slide = request.env['slide.slide'].sudo().search([('id', '=', int(slide_id))])
        total_question = len(slide.quiz_question_ids)
        for question in slide.quiz_question_ids:
            answer = request.env['slide.answer'].sudo().search([
                ('quiz_answer_line_id', '=', question.id),
                ('is_correct', '=', True)])
            qust_answer = answer_set.get(str(question.id))
            if(not qust_answer):
                not_attempt = not_attempt + 1
            if(answer.ids == qust_answer):
                correct_answer = correct_answer + 1
        percent = int(int(correct_answer) / int(total_question) * 100)

        """ Create a quiz log while student login"""
        if request.env.uid != 4:
            student = request.env['res.users'].browse(request.uid)
            content_subscrib = request.env['slide.content.subscribed'].sudo().search([
                    ('res_partner_id', '=', student.partner_id.id)],
                    order='seq_no desc', limit=1)
            if(val.get(kw.get('question_id'))):
                exit_quiz_log = request.env['quiz.log'].sudo().search([
                        ('question_id', '=', int(kw.get('question_id'))),
                        ('content_subscribed_id', '=', content_subscrib.id)])
                if not exit_quiz_log:
                    stud_choose = val.get(kw.get('question_id'))
                    status = 'wrong'
                    stud_answer = request.env['slide.answer'].sudo().search([('id', 'in', stud_choose)])
                    answer = request.env['slide.answer'].sudo().search([
                            ('quiz_answer_line_id', '=', int(kw.get('question_id'))),
                            ('is_correct', '=', True)])
                    if(stud_answer.ids == answer.ids):
                        status = 'correct'
                    request.env['quiz.log'].sudo().create({
                            'question_id': int(kw.get('question_id')),
                            'content_subscribed_id': content_subscrib.id,
                            'answer_id': [(6, 0, stud_answer.ids)],
                            'partner_id': student.partner_id.id,
                            'status': status
                            })
        values = {'total_question': total_question,
                  'correct_answer': correct_answer,
                  'percent': str(percent)+"%",
                  'not_attempt': not_attempt
                  }
        request.session['quiz_answer'] = {}
        return request.env['ir.ui.view'].render_template("skit_slide.quiz_result_view", values)
    
    @http.route(['/user-role/student_parent/detail'], type='json',
                auth="public", methods=['POST'], website=True)
    def student_parent_detail(self, **kw):
        parents = []
        if(kw.get('user_partner_id')):
            partner_id = request.env['res.partner'].sudo().search(
                                                    [('id', '=',
                                                      kw.get('user_partner_id'))
                                                     ])
            for parent in partner_id.slide_parents:
                parents.append({'parent_name': parent.name,
                                'parent_email': parent.email,
                                })
        values = {
                  'parents': parents,
                  }
        return request.env['ir.ui.view'].render_template(
                        "skit_slide.website_student_parent_details", values)

    @http.route(['/user-role/parent_child/detail'], type='json',
                auth="public", methods=['POST'], website=True)
    def parent_child_detail(self, **kw):
        childs = []
        if(kw.get('user_partner_id')):
            partner_id = request.env['res.partner'].sudo().search(
                                                    [('id', '=',
                                                      kw.get('user_partner_id'))
                                                     ])
            for student in partner_id.student_id:
                childs.append({'child_name': student.name,
                               'child_email': student.email,
                               })
        values = {
                  'childs': childs,
                  }
        return request.env['ir.ui.view'].render_template(
                         "skit_slide.website_parent_child_details", values)

    @http.route('/grades-subjects/details', type='json', auth="public", methods=['POST'], website=True)
    def grade_subject(self, **kw):
        grades = request.env['product.category'].sudo().search([('is_grade', '=', True)])
        values = {'grades': grades}
        return request.env['ir.ui.view'].render_template('skit_slide.website_grade_subjects_details', values)

    @http.route('/create_parent/details', type='json',
                auth="public", methods=['POST'], website=True)
    def create_parent(self, **kw):
        user_partner_id = int(kw.get('user_partner_id'))
        parent_ids = request.env['res.partner'].sudo().search(
                                                    [('id', '=',
                                                      user_partner_id)
                                                     ])
        res_parent_id = request.env['res.partner'].sudo().search(
                                [('isparent', '=', True),
                                 ('id', 'not in',
                                  parent_ids.slide_parents.ids),
                                 ], order='id')

        values = {'res_parent_id': res_parent_id,
                  'user_partner_id': user_partner_id
                  }
        return request.env['ir.ui.view'].render_template('skit_slide.add_parent_popup', values)

