import pytest


@pytest.fixture
def make_permission_assertions(assert_response_errors):
    def evaluate(assertion, path=None):
        if hasattr(assertion, '__call__'):
            assert path is not None, \
                "Assertion can only be a callable if the path is variable " \
                "and provided."
            return assertion(path)
        return assertion

    def status_assertion_message(case, response, status_code, path=None):
        if path:
            return (
                f"The expected status code for path {path}, case {case}, "
                f"was {status_code}, but the response had status code "
                f"{response.status_code}."
            )
        return (
            f"The expected status code for case {case} was {status_code}, "
            f"but the response had status code {response.status_code}."
        )

    def inner(response, case, assertions, path=None):
        assert isinstance(assertions, dict), "Assertions must be a dictionary."
        if 'status' in assertions:
            status_code = evaluate(assertions['status'], path=path)
            assert response.status_code == status_code, \
                status_assertion_message(case, response, status_code, path)

        if 'error' in assertions:
            error = evaluate(assertions['error'], path=path)
            assert_response_errors(response, error)
    return inner
