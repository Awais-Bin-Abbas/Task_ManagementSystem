# teams/views.py
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from rest_framework import views, status, permissions
from rest_framework.response import Response
from .models import Team
from .serializers import TeamSerializer


class TeamAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeamSerializer

    @extend_schema(
        summary="Create a new team",
        description="Only Admin or Manager can create teams. Requires JWT authentication.",
        request=TeamSerializer,
        responses={
            201: TeamSerializer,
            400: OpenApiExample("Invalid data", value={"error": "Invalid data!"}),
            401: OpenApiExample("Unauthorized", value={"error": "Only Admin/Manager can create teams"}),
        },
        examples=[
            OpenApiExample(
                "Create Team Example",
                value={"name": "Dev Team", "description": "Backend development team"},
                request_only=True,
            )
        ],
        tags=["Teams"]
    )
    def post(self, request):
        user = request.user
        if user.is_superuser or user.role == "Manager":
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({"error": "Invalid data!"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "Only Admin/Manager can create teams"}, status=status.HTTP_401_UNAUTHORIZED)

    @extend_schema(
        summary="Get all teams or a single team",
        description="Returns all teams. Pass `id` as query param to get a single team.",
        parameters=[
            OpenApiParameter(name="id", description="ID of the team", required=False, type=int)
        ],
        responses={
            200: TeamSerializer(many=True),
            404: OpenApiExample("Not found", value={"error": "Team not found"}),
        },
        tags=["Teams"]
    )
    def get(self, request):
        team_id = request.query_params.get("id")
        if team_id:
            team = Team.objects.filter(id=team_id).first()
            if not team:
                return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.serializer_class(team)
            return Response(serializer.data, status=status.HTTP_200_OK)
        teams = Team.objects.all()
        serializer = self.serializer_class(teams, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Partially update a team",
        description="Update one or more fields of a team. Pass `id` in the request body.",
        request=TeamSerializer,
        responses={
            200: TeamSerializer,
            400: OpenApiExample("Bad request", value={"error": "Team id required"}),
            404: OpenApiExample("Not found", value={"error": "Team not found"}),
        },
        tags=["Teams"]
    )
    def patch(self, request):
        team_id = request.data.get("id")
        if not team_id:
            return Response({"error": "Team id required"}, status=status.HTTP_400_BAD_REQUEST)
        team = Team.objects.filter(id=team_id).first()
        if not team:
            return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(team, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete a team",
        description="Delete a team by ID passed as a URL parameter. Cascades to projects.",
        responses={
            200: OpenApiExample("Success", value={"success": "Team deleted successfully"}),
            400: OpenApiExample("Bad request", value={"error": "Team id required"}),
            404: OpenApiExample("Not found", value={"error": "Team not found"}),
        },
        tags=["Teams"]
    )
    def delete(self, request, id=None):
        if not id:
            return Response({"error": "Team id required"}, status=status.HTTP_400_BAD_REQUEST)
        team = Team.objects.filter(id=id).first()
        if not team:
            return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)
        team.delete()
        return Response({"success": "Team deleted successfully"}, status=status.HTTP_200_OK)