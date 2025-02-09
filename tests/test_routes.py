"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"

HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}

######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        talisman.force_https = False
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_read_an_account(self):
        """It should Read a single Account"""
        account = self._create_accounts(1)[0]
        post_response=self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(
            post_response.status_code,
            status.HTTP_201_CREATED,
            "Account_creation_failed"
        )
        #Extract the account id from the creation response
        new_account = post_response.get_json()
        account_id = new_account["id"]

        #Read the account using the account id
        get_response = self.client.get(f"{BASE_URL}/{account_id}")
        self.assertEqual(
            get_response.status_code,
            status.HTTP_200_OK,
            "Reading the account did not return HTTP_200_OK "
        )

        # Verify that the returned data matches what was sent
        retrieved_account = get_response.get_json()
        self.assertEqual(retrieved_account["name"], account.name)
        self.assertEqual(retrieved_account["email"], account.email)
        self.assertEqual(retrieved_account["address"], account.address)
        self.assertEqual(retrieved_account["phone_number"], account.phone_number)
        self.assertEqual(retrieved_account["date_joined"], str(account.date_joined))

    def test_account_not_found(self):
        """It should not Read an Account that is not found"""
        get_response=self.client.get(f"{BASE_URL}/0")
        self.assertEqual(
            get_response.status_code, 
            status.HTTP_404_NOT_FOUND, 
            f"Expected 404 when reading non-existant account, got {get_response.status_code} instead" 
            )
    
    # test out the list of the accounts    
    def test_to_list_out_accounts(self):
        """It should Get a list of Accounts"""
        self._create_accounts(5)
        # send a self.client.get() request to the BASE_URL
        response=self.client.get(BASE_URL)
        
        # assert that the resp.status_code is status.HTTP_200_OK
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            f"Expect to get status 200, but got {response.status_code} instead."
        )
        # get the data from resp.get_json()
        get_accounts = response.get_json()
        # assert that the len() of the data is 5 (the number of accounts you created)
        self.assertEqual(
            len(get_accounts),
            5,
            f"Expect to get 5 accounts back, but got {len(get_accounts)} instead.")
        

    # test the update method for accounts
    def test_update_account(self):
        """It should Update an existing Account"""
        # create an Account to update
        test_account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=test_account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(
            response.status_code, 
            status.HTTP_201_CREATED, 
            f"Expect to get HTTP_201_CREATED, but got {response.status_code} instead."
        )

        # update the account
        new_account = response.get_json()
        new_account_id = new_account["id"]
        new_account["name"] = "Thuy Anh"
        
        new_response = self.client.put(
            f"{BASE_URL}/{new_account_id}",  # URL for personal account
            json=new_account,
            content_type="application/json"
        )
        
        self.assertEqual(
            new_response.status_code,
            status.HTTP_200_OK,
            f"Expected HTTP_200_OK but got {new_response.status_code} instead."
        )
        
        # verify that name was updated
        updated_account = new_response.get_json()
        self.assertIn("name", updated_account, "Response JSON does not contain 'name' field")
        self.assertEqual(
            updated_account["name"], 
            "Thuy Anh",
            "Name of the Account hasn't been updated."
        )

    def test_delete_account(self):
        """It should Delete an Account"""
        account = self._create_accounts(1)[0]
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(
            response.status_code, 
            status.HTTP_201_CREATED, 
            f"Expect to get HTTP_201_CREATED, but got {response.status_code} instead."
        )
        new_account = response.get_json()
        #Extract the account id from the creation response
        account_id = new_account["id"]

        #Read the account using the account id
        get_response = self.client.delete(
            f"{BASE_URL}/{account_id}"
            )
        self.assertEqual(
            get_response.status_code,
            status.HTTP_204_NO_CONTENT,
            f"Delete the account did not return HTTP_204_NO_CONTENT. Instead {get_response.status_code} "
        )
        followup_response = self.client.get(f"{BASE_URL}/{account_id}")
        self.assertEqual(
            followup_response.status_code,
            status.HTTP_404_NOT_FOUND,
            f"Expected 404 when trying to read a deleted account, but got {followup_response.status_code}"
        )

    def test_method_not_allowed(self):
        """It should not allow an illegal method call"""
        resp = self.client.delete(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_security_headers(self):
        """It should return security headers"""
        # Create a test client
        client = app.test_client()

        # Make a request to the root URL with HTTPS enforced
        response = client.get("/", environ_overrides = HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Response problematic from server.")
        # Extract headers from the response
        headers = response.headers

        #Assert the presence of security headers
        assert headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("Content-Security-Policy") == "default-src 'self'; object-src 'none'"
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

        print("✅ Security headers test passed!")