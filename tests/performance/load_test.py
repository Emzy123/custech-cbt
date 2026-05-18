"""
Performance and load testing for CBT system.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import httpx
import pytest
pytest.skip(
    "Performance suite requires dedicated infra and endpoint contract migration.",
    allow_module_level=True,
)
from locust import HttpUser, task, between
import psutil
import json

from tests.conftest import load_test_config, performance_test_data


class CBTLoadTest(HttpUser):
    """Load testing user simulation."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a simulated user starts."""
        self.token = None
        self.user_data = None
        
    @task(3)
    def login(self):
        """Simulate user login."""
        if not self.token:
            # Generate test user data
            import random
            import string
            
            email = f"{''.join(random.choices(string.ascii_lowercase, k=8))}@test.edu"
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            
            login_data = {
                "email": email,
                "password": password
            }
            
            response = self.client.post("/api/v1/auth/login", json=login_data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get("access_token")
                self.user_data = {"email": email, "password": password}
    
    @task(2)
    def get_questions(self):
        """Simulate fetching questions."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            self.client.get("/api/v1/questions", headers=headers)
    
    @task(2)
    def get_examinations(self):
        """Simulate fetching examinations."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            self.client.get("/api/v1/examinations", headers=headers)
    
    @task(1)
    def get_profile(self):
        """Simulate fetching user profile."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            self.client.get("/api/v1/students/profile", headers=headers)
    
    @task(1)
    def submit_exam(self):
        """Simulate exam submission."""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Mock exam submission data
            submission_data = {
                "examination_id": "test-exam-id",
                "answers": [
                    {"question_id": "q1", "selected_option": "A"},
                    {"question_id": "q2", "selected_option": "B"}
                ],
                "time_taken_minutes": 45
            }
            
            self.client.post("/api/v1/examinations/submit", json=submission_data, headers=headers)


@pytest.mark.performance
class TestPerformance:
    """Performance test suite."""
    
    @pytest.fixture
    def load_config(self):
        """Load test configuration."""
        return load_test_config()
    
    @pytest.fixture
    def test_data(self):
        """Performance test data."""
        return performance_test_data()
    
    @pytest.mark.asyncio
    async def test_concurrent_login_performance(self, authenticated_client, load_config):
        """Test concurrent login performance."""
        concurrent_users = load_config["concurrent_users"]
        ramp_up_time = load_config["ramp_up_seconds"]
        
        # Test data
        users = [
            {
                "email": f"testuser{i}@test.edu",
                "password": f"password{i}"
            }
            for i in range(concurrent_users)
        ]
        
        # Performance metrics
        response_times = []
        error_count = 0
        success_count = 0
        
        async def login_user(user_data):
            """Login a single user."""
            start_time = time.time()
            try:
                response = await authenticated_client.post("/api/v1/auth/login", json=user_data)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                if response.status_code == 200:
                    return {"success": True, "response_time": response_time}
                else:
                    return {"success": False, "response_time": response_time}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Execute concurrent logins
        tasks = [login_user(user) for user in users]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, dict):
                if result.get("success"):
                    success_count += 1
                    response_times.append(result["response_time"])
                else:
                    error_count += 1
            else:
                error_count += 1
        
        # Calculate performance metrics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        error_rate = error_count / len(users)
        throughput = success_count / (ramp_up_time + 1)  # requests per second
        
        # Assertions based on performance thresholds
        thresholds = load_config["performance_thresholds"]
        
        assert p95_response_time <= thresholds["response_time_p95"], \
            f"P95 response time {p95_response_time}ms exceeds threshold {thresholds['response_time_p95']}ms"
        
        assert p99_response_time <= thresholds["response_time_p99"], \
            f"P99 response time {p99_response_time}ms exceeds threshold {thresholds['response_time_p99']}ms"
        
        assert error_rate <= thresholds["error_rate"], \
            f"Error rate {error_rate} exceeds threshold {thresholds['error_rate']}"
        
        assert throughput >= thresholds["throughput_min"], \
            f"Throughput {throughput} rps below threshold {thresholds['throughput_min']} rps"
        
        # Report results
        performance_report = {
            "test_name": "concurrent_login_performance",
            "concurrent_users": concurrent_users,
            "success_count": success_count,
            "error_count": error_count,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "p95_response_time": p95_response_time,
            "p99_response_time": p99_response_time,
            "throughput": throughput,
            "thresholds_met": all([
                p95_response_time <= thresholds["response_time_p95"],
                p99_response_time <= thresholds["response_time_p99"],
                error_rate <= thresholds["error_rate"],
                throughput >= thresholds["throughput_min"]
            ])
        }
        
        print(f"\nPerformance Report: {json.dumps(performance_report, indent=2)}")
    
    @pytest.mark.asyncio
    async def test_api_endpoint_performance(self, authenticated_client, load_config):
        """Test performance of various API endpoints."""
        endpoints = load_config["target_endpoints"]
        response_times = {}
        
        for endpoint in endpoints:
            endpoint_times = []
            error_count = 0
            
            # Make multiple requests to each endpoint
            for _ in range(50):  # 50 requests per endpoint
                start_time = time.time()
                try:
                    if endpoint == "/api/v1/auth/login":
                        response = await authenticated_client.post(endpoint, json={
                            "email": "test@test.edu",
                            "password": "password"
                        })
                    else:
                        response = await authenticated_client.get(endpoint)
                    
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000
                    
                    if response.status_code == 200:
                        endpoint_times.append(response_time)
                    else:
                        error_count += 1
                        
                except Exception:
                    error_count += 1
            
            # Calculate metrics for this endpoint
            if endpoint_times:
                response_times[endpoint] = {
                    "avg_response_time": statistics.mean(endpoint_times),
                    "p95_response_time": statistics.quantiles(endpoint_times, n=20)[18],
                    "p99_response_time": statistics.quantiles(endpoint_times, n=100)[98],
                    "min_response_time": min(endpoint_times),
                    "max_response_time": max(endpoint_times),
                    "error_count": error_count,
                    "success_rate": len(endpoint_times) / 50
                }
            else:
                response_times[endpoint] = {
                    "avg_response_time": 0,
                    "p95_response_time": 0,
                    "p99_response_time": 0,
                    "min_response_time": 0,
                    "max_response_time": 0,
                    "error_count": 50,
                    "success_rate": 0
                }
        
        # Assert performance requirements
        thresholds = load_config["performance_thresholds"]
        
        for endpoint, metrics in response_times.items():
            assert metrics["p95_response_time"] <= thresholds["response_time_p95"], \
                f"Endpoint {endpoint} P95 response time {metrics['p95_response_time']}ms exceeds threshold"
            
            assert metrics["success_rate"] >= (1 - thresholds["error_rate"]), \
                f"Endpoint {endpoint} success rate {metrics['success_rate']} below threshold"
        
        print(f"\nEndpoint Performance Report: {json.dumps(response_times, indent=2)}")
    
    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self, test_session, load_config):
        """Test database connection pool performance."""
        connection_times = []
        query_times = []
        
        # Test connection acquisition time
        for _ in range(100):
            start_time = time.time()
            
            # Simulate database operation
            result = await test_session.execute("SELECT 1")
            await result.fetchone()
            
            end_time = time.time()
            connection_times.append((end_time - start_time) * 1000)
        
        # Test query performance
        for _ in range(50):
            start_time = time.time()
            
            # Simulate complex query
            result = await test_session.execute("SELECT COUNT(*) FROM users")
            await result.fetchone()
            
            end_time = time.time()
            query_times.append((end_time - start_time) * 1000)
        
        # Calculate metrics
        avg_connection_time = statistics.mean(connection_times)
        p95_connection_time = statistics.quantiles(connection_times, n=20)[18]
        avg_query_time = statistics.mean(query_times)
        p95_query_time = statistics.quantiles(query_times, n=20)[18]
        
        # Performance assertions
        assert avg_connection_time <= 100, \
            f"Average connection time {avg_connection_time}ms exceeds 100ms threshold"
        
        assert p95_connection_time <= 200, \
            f"P95 connection time {p95_connection_time}ms exceeds 200ms threshold"
        
        assert avg_query_time <= 50, \
            f"Average query time {avg_query_time}ms exceeds 50ms threshold"
        
        print(f"\nDatabase Performance Report:")
        print(f"Average connection time: {avg_connection_time:.2f}ms")
        print(f"P95 connection time: {p95_connection_time:.2f}ms")
        print(f"Average query time: {avg_query_time:.2f}ms")
        print(f"P95 query time: {p95_query_time:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_redis_cache_performance(self, test_redis, load_config):
        """Test Redis cache performance."""
        # Test write performance
        write_times = []
        for i in range(1000):
            key = f"test_key_{i}"
            value = f"test_value_{i}" * 100  # Larger value
            
            start_time = time.time()
            await test_redis.set(key, value, ex=3600)
            end_time = time.time()
            
            write_times.append((end_time - start_time) * 1000)
        
        # Test read performance
        read_times = []
        for i in range(1000):
            key = f"test_key_{i}"
            
            start_time = time.time()
            await test_redis.get(key)
            end_time = time.time()
            
            read_times.append((end_time - start_time) * 1000)
        
        # Calculate metrics
        avg_write_time = statistics.mean(write_times)
        p95_write_time = statistics.quantiles(write_times, n=20)[18]
        avg_read_time = statistics.mean(read_times)
        p95_read_time = statistics.quantiles(read_times, n=20)[18]
        
        # Performance assertions
        assert avg_write_time <= 10, \
            f"Average Redis write time {avg_write_time}ms exceeds 10ms threshold"
        
        assert avg_read_time <= 5, \
            f"Average Redis read time {avg_read_time}ms exceeds 5ms threshold"
        
        print(f"\nRedis Performance Report:")
        print(f"Average write time: {avg_write_time:.2f}ms")
        print(f"P95 write time: {p95_write_time:.2f}ms")
        print(f"Average read time: {avg_read_time:.2f}ms")
        print(f"P95 read time: {p95_read_time:.2f}ms")
        
        # Cleanup
        for i in range(1000):
            await test_redis.delete(f"test_key_{i}")
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, load_config):
        """Test memory usage under load."""
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate load
        concurrent_tasks = []
        
        async def memory_intensive_task():
            """Memory intensive task."""
            data = []
            for i in range(10000):
                data.append({
                    "id": i,
                    "data": "x" * 1000,  # 1KB per item
                    "timestamp": time.time()
                })
                if i % 1000 == 0:
                    await asyncio.sleep(0.01)  # Yield control
            return len(data)
        
        # Execute concurrent memory-intensive tasks
        for _ in range(10):
            concurrent_tasks.append(memory_intensive_task())
        
        results = await asyncio.gather(*concurrent_tasks)
        
        # Get peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory usage assertions
        assert memory_increase <= 500, \
            f"Memory increase {memory_increase}MB exceeds 500MB threshold"
        
        print(f"\nMemory Usage Report:")
        print(f"Initial memory: {initial_memory:.2f}MB")
        print(f"Peak memory: {peak_memory:.2f}MB")
        print(f"Memory increase: {memory_increase:.2f}MB")
        print(f"Tasks completed: {len(results)}")
    
    @pytest.mark.asyncio
    async def test_cpu_usage_under_load(self, load_config):
        """Test CPU usage under load."""
        # Get initial CPU usage
        initial_cpu = psutil.cpu_percent(interval=1)
        
        # Simulate CPU-intensive load
        async def cpu_intensive_task():
            """CPU intensive task."""
            result = 0
            for i in range(1000000):
                result += i * i
            return result
        
        # Execute concurrent CPU-intensive tasks
        start_time = time.time()
        concurrent_tasks = [cpu_intensive_task() for _ in range(20)]
        results = await asyncio.gather(*concurrent_tasks)
        end_time = time.time()
        
        # Get CPU usage during load
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # CPU usage assertions
        assert cpu_usage <= 80, \
            f"CPU usage {cpu_usage}% exceeds 80% threshold"
        
        print(f"\nCPU Usage Report:")
        print(f"Initial CPU usage: {initial_cpu}%")
        print(f"Peak CPU usage: {cpu_usage}%")
        print(f"Tasks completed: {len(results)}")
        print(f"Execution time: {end_time - start_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_stress_test_sustained_load(self, authenticated_client, load_config):
        """Test sustained load over time."""
        duration = load_config["duration_seconds"] // 10  # Reduced for testing
        concurrent_users = 10  # Reduced for testing
        
        # Metrics collection
        response_times = []
        error_count = 0
        success_count = 0
        
        async def sustained_load_task():
            """Sustained load task."""
            nonlocal error_count, success_count
            
            end_time = time.time() + duration
            
            while time.time() < end_time:
                start_time = time.time()
                try:
                    response = await authenticated_client.get("/api/v1/questions")
                    end_time_req = time.time()
                    response_time = (end_time_req - start_time) * 1000
                    
                    if response.status_code == 200:
                        success_count += 1
                        response_times.append(response_time)
                    else:
                        error_count += 1
                        
                except Exception:
                    error_count += 1
                
                await asyncio.sleep(0.1)  # 10 requests per second per user
        
        # Execute sustained load
        tasks = [sustained_load_task() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks)
        
        # Calculate metrics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]
        else:
            avg_response_time = p95_response_time = 0
        
        error_rate = error_count / (success_count + error_count) if (success_count + error_count) > 0 else 0
        throughput = success_count / duration
        
        # Performance assertions
        thresholds = load_config["performance_thresholds"]
        
        assert p95_response_time <= thresholds["response_time_p95"], \
            f"Sustained load P95 response time {p95_response_time}ms exceeds threshold"
        
        assert error_rate <= thresholds["error_rate"], \
            f"Sustained load error rate {error_rate} exceeds threshold"
        
        print(f"\nSustained Load Report:")
        print(f"Duration: {duration}s")
        print(f"Concurrent users: {concurrent_users}")
        print(f"Success count: {success_count}")
        print(f"Error count: {error_count}")
        print(f"Error rate: {error_rate:.2%}")
        print(f"Average response time: {avg_response_time:.2f}ms")
        print(f"P95 response time: {p95_response_time:.2f}ms")
        print(f"Throughput: {throughput:.2f} rps")


@pytest.mark.performance
class TestLoadScenarios:
    """Load testing scenarios."""
    
    @pytest.mark.asyncio
    async def test_exam_submission_load(self, authenticated_client, test_data):
        """Test load during exam submission."""
        submissions = []
        response_times = []
        
        async def submit_exam():
            """Submit exam."""
            import random
            
            submission_data = {
                "examination_id": "test-exam-id",
                "answers": [
                    {
                        "question_id": f"q{random.randint(1, 50)}",
                        "selected_option": random.choice(["A", "B", "C", "D"])
                    }
                    for _ in range(50)
                ],
                "time_taken_minutes": random.randint(30, 120)
            }
            
            start_time = time.time()
            response = await authenticated_client.post(
                "/api/v1/examinations/submit",
                json=submission_data
            )
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)
            
            return response.status_code == 200
        
        # Execute concurrent exam submissions
        tasks = [submit_exam() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        # Calculate metrics
        success_count = sum(results)
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]
        
        # Assertions
        assert success_count >= 95, f"Only {success_count}/100 submissions succeeded"
        assert p95_response_time <= 5000, f"P95 response time {p95_response_time}ms exceeds 5s"
        
        print(f"\nExam Submission Load Report:")
        print(f"Successful submissions: {success_count}/100")
        print(f"Average response time: {avg_response_time:.2f}ms")
        print(f"P95 response time: {p95_response_time:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_proctoring_system_load(self, authenticated_client, test_data):
        """Test load on proctoring system."""
        proctoring_events = []
        
        async def simulate_proctoring_event():
            """Simulate proctoring event."""
            import random
            
            event_data = {
                "event_type": random.choice(["focus_loss", "fullscreen_exit", "keyboard_violation"]),
                "duration": random.uniform(0.1, 5.0),
                "reason": random.choice(["tab_switch", "user_action", "system_notification"])
            }
            
            start_time = time.time()
            response = await authenticated_client.post(
                "/api/v1/proctoring/session/test-session/focus-loss",
                json=event_data
            )
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            proctoring_events.append(response_time)
            
            return response.status_code == 200
        
        # Execute concurrent proctoring events
        tasks = [simulate_proctoring_event() for _ in range(200)]
        results = await asyncio.gather(*tasks)
        
        # Calculate metrics
        success_count = sum(results)
        avg_response_time = statistics.mean(proctoring_events)
        p95_response_time = statistics.quantiles(proctoring_events, n=20)[18]
        
        # Assertions
        assert success_count >= 190, f"Only {success_count}/200 proctoring events succeeded"
        assert p95_response_time <= 1000, f"P95 response time {p95_response_time}ms exceeds 1s"
        
        print(f"\nProctoring System Load Report:")
        print(f"Successful events: {success_count}/200")
        print(f"Average response time: {avg_response_time:.2f}ms")
        print(f"P95 response time: {p95_response_time:.2f}ms")
