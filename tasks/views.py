from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone

from .models import Task
from .serializers import TaskSerializer
from projects.models import Project
from accounts.models import User
from pagination import StandardPagination  

class TaskAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer
    pagination_class = StandardPagination


    # CREATE TASK
    def post(self, request):

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


    # GET ALL OR SINGLE TASK
    def get(self, request):
            task_id = request.query_params.get("id")

            # single task — no pagination needed
            if task_id:
                task = Task.objects.filter(id=task_id).first()
                if not task:
                    return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
                serializer = self.serializer_class(task)
                return Response(serializer.data)
                    
            # list — apply pagination
            tasks = Task.objects.all().order_by('id')
            paginator = StandardPagination()
            paginated_tasks = paginator.paginate_queryset(tasks, request)
            serializer = self.serializer_class(paginated_tasks, many=True)
            return paginator.get_paginated_response(serializer.data)    



    # UPDATE TASK
    def patch(self, request):

        task_id = request.data.get("id")

        if not task_id:
            return Response({"error": "Task id required"}, status=status.HTTP_400_BAD_REQUEST)

        task = Task.objects.filter(id=task_id).first()

        if not task:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(task, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    # DELETE TASK
    def delete(self, request, id=None):

        if not id:
            return Response({"error": "Task id required"}, status=status.HTTP_400_BAD_REQUEST)

        task = Task.objects.filter(id=id).first()

        if not task:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        task.delete()

        return Response({"message": "Task deleted successfully"})