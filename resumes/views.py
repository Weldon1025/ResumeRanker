import mimetypes
import os

from django.conf import settings
from django.http.response import HttpResponse
from django.shortcuts import render
from django.contrib import messages
# import Auth model
from django.contrib.auth.models import User
from .models import CandidateResumes, HRJobPostings, AppliedJobs
import PyPDF2
import pickle
from .matchResumes import get_cosine_sim
from .resumeClassification import classify_resume

def resume_download(request, user_id):
    candidate_resume = CandidateResumes.objects.get(user_id=user_id)
    file_path = os.path.join(settings.MEDIA_ROOT, candidate_resume.resume_file.name)
    f = open(file_path, "rb")
    mime_type, _ = mimetypes.guess_type(file_path)
    # Set the return value of the HttpResponse
    response = HttpResponse(f, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % candidate_resume.resume_file.name
    return response


def jobdescription_download(request, job_id):
    job_description = HRJobPostings.objects.get(id=job_id).description_file
    file_path = os.path.join(settings.MEDIA_ROOT, job_description.name)
    f = open(file_path, "rb")
    mime_type, _ = mimetypes.guess_type(file_path)
    # Set the return value of the HttpResponse
    response = HttpResponse(f, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % job_description.name
    return response


def HRJobPostView(request):
    if request.method == 'GET':
        if request.user.is_superuser:
            job_list = HRJobPostings.objects.filter(user=request.user)
            return render(request, 'resumes/hr_job_post.html', {'job_list': job_list})


def AppliedCandidates(request, job_id):
    if request.method == 'GET':
        applied_candidates = AppliedJobs.objects.filter(job_posting_id=job_id).select_related('candidate')
        if len(applied_candidates) == 0:
            messages.error(request, 'No candidates applied for this job')
            return render(request, 'resumes/applied_candidates.html')
        users = []
        resumes = []
        for user in applied_candidates:
            users.append(user.candidate.user_id)
            resumes.append(user.candidate.resume_file)
        # get matching skills
        job_description_file = HRJobPostings.objects.get(id=job_id).description_file
        description_file_path = os.path.join(settings.MEDIA_ROOT, job_description_file.name)
        job_description = PyPDF2.PdfFileReader(description_file_path)
        job_description_text = job_description.getPage(0).extractText()

        match_percentage = []
        classified_jobs = []
        for resume in resumes:
            pdffileobject = open(os.path.join(settings.MEDIA_ROOT, str(resume)), 'rb')
            pdfReader = PyPDF2.PdfFileReader(pdffileobject)
            x = pdfReader.numPages
            pageObj = pdfReader.getPage(x - 1)
            text = pageObj.extractText()
            match_percentage.append(get_cosine_sim(text, job_description_text))
            classified_jobs.append(classify_resume(text))
        user_details = User.objects.filter(id__in=users)
        final = []
        for user in user_details:
            final.append({'id': user.id, 'name': user.first_name + ' ' + user.last_name, 'email': user.email,
                          'resume': resumes[users.index(user.id)],
                          'matching_percentage': match_percentage[users.index(user.id)],
                          'classified_jobs': classified_jobs[users.index(user.id)]})
        print(final)
        return render(request, 'resumes/applied_candidates.html', {'all_details': final})


def UploadResume(request):
    if request.method == 'GET':
        return render(request, 'resumes/upload_resume.html')

    if request.method == 'POST':

        resume = request.FILES['resume']
        allowed_extension = settings.ALLOWED_EXTENSIONS
        if resume.name.split('.')[-1] in allowed_extension:
            if CandidateResumes.objects.filter(user=request.user).exists():
                CandidateResumes.objects.get(user=request.user).delete()
                CandidateResumes.objects.create(user=request.user, resume_file=resume)
                messages.success(request, 'Resume Updated successfully')
                return render(request, 'resumes/upload_resume.html', {'message': 'Resume updated successfully'})
            else:
                CandidateResumes(
                    user=request.user,
                    resume_file=resume).save()

                messages.success(request, 'Resume uploaded successfully')
                return render(request, 'resumes/upload_resume.html', {'message': 'Resume uploaded successfully'})
        else:
            messages.error(request, 'Please upload a valid PDF, or word file')


def JobListView(request):
    if request.method == 'GET':
        job_list = HRJobPostings.objects.all()
        return render(request, 'resumes/job_list.html', {'job_list': job_list})


def ApplyForJob(request, job_id):
    if request.method == 'GET':
        job = HRJobPostings.objects.get(id=job_id)
        candidate = CandidateResumes.objects.get(user=request.user)
        # check if already applied for job
        if AppliedJobs.objects.filter(candidate=candidate, job_posting=job).exists():
            messages.warning(request, 'You have already applied for this job')
            return render(request, 'resumes/job_list.html', {'message': 'You already applied for this job'})
        else:
            AppliedJobs(
                job_posting=job,
                candidate=candidate,
            ).save()
            messages.success(request, 'You have successfully applied for the job')
            return render(request, 'resumes/job_list.html', {'message': 'You have successfully applied for the job'})
    else:
        messages.error(request, 'You are not authorized to apply for the job')
        return render(request, 'resumes/job_list.html', {'message': 'You are not authorized to apply for the job'})


def HRJobPost(request):
    if request.method == 'GET':
        return render(request, 'resumes/add_job_posting.html')
    elif request.method == 'POST':
        title = request.POST['title']
        location = request.POST['location']
        joining_date = request.POST['joining_date']
        skills = request.POST['skills']
        job_description_file = request.FILES['job_description_file']

        if request.user.is_staff:
            job_details = HRJobPostings(
                job_title=title,
                job_location=location,
                skills_required=skills,
                joining_date=joining_date,
                user=request.user)
            job_details.save()
            # Saving the job description file
            if job_description_file.name.split('.')[-1] in settings.ALLOWED_EXTENSIONS:
                job_details.description_file = request.FILES['job_description_file']
                job_details.save()
                messages.success(request, 'Job posting added successfully')
                return render(request, 'resumes/add_job_posting.html', {'message': 'Job posting added successfully'})
            else:
                messages.error(request, 'Please upload a valid PDF, or word file')
                return render(request, 'resumes/add_job_posting.html', {'message': 'Please upload a valid PDF, or '
                                                                                   'word file'})
        else:
            messages.error(request, 'You are not authorized to add job postings')
            return render(request, 'resumes/add_job_posting.html', {'message': 'You are not authorized to add job '
                                                                               'postings'})


def deleteJobPost(request, job_id):
    if request.method == 'GET':
        user = request.user
        job = HRJobPostings.objects.get(id=job_id, user=user)
        if job:
            job.delete()
            messages.success(request, 'Job posting deleted successfully')
            return render(request, 'resumes/job_list.html', {'message': 'Job posting deleted successfully'})
        else:
            messages.error(request, 'You are not authorized to delete this job posting')
            return render(request, 'resumes/job_list.html', {'message': 'You are not authorized to delete this job '
                                                                        'posting'})
