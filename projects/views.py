from rest_framework import views, status, permissions
from rest_framework.response import Response
from .models import Project
from .serializers import ProjectSerializer


class ProjectAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer

    # Create Project
    def post(self, request):
        user = request.user

        if user.is_superuser or getattr(user, "role", None) == "Manager":
            serializer = self.serializer_class(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Only Admin/Manager can create projects"},status=status.HTTP_401_UNAUTHORIZED
        )

    # Get all projects or single project by query param id
    def get(self, request):
        project_id = request.query_params.get("id")  # get id from query params

        if project_id:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = self.serializer_class(project)
            return Response(serializer.data, status=status.HTTP_200_OK)

        projects = Project.objects.all()
        serializer = self.serializer_class(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Partial update using query param id
    def patch(self, request):
        project_id = request.query_params.get("id")  # get id from query params
        if not project_id:
            return Response({"error": "Project id required in query params"},status=status.HTTP_400_BAD_REQUEST)

        project = Project.objects.filter(id=project_id).first()
        if not project:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Delete using query param id
    def delete(self, request):
        project_id = request.query_params.get("id")  # get id from query params
        if not project_id:
            return Response({"error": "Project id required in query params"},status=status.HTTP_400_BAD_REQUEST)

        project = Project.objects.filter(id=project_id).first()
        if not project:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        project.delete()
        return Response({"success": "Project deleted successfully"}, status=status.HTTP_200_OK)