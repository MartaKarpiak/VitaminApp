from locust import HttpUser, task, between


class VitaminUser(HttpUser):

    wait_time = between(1, 3)

    @task
    def home(self):
        self.client.get("/")

    @task
    def login_page(self):
        self.client.get("/login")

    @task
    def forgot_password(self):
        self.client.get("/forgot-password")

    @task
    def dashboard(self):
        self.client.get("/dashboard")