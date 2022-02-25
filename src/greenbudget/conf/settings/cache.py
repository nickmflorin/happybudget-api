from greenbudget.conf import config, Environments

ELASTICACHE_ENDPOINT = config(
    name='ELASTICACHE_ENDPOINT',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: '',
        Environments.LOCAL: ''
    }
)

CACHE_ENABLED = False

CACHE_LOCATION = f"redis://{ELASTICACHE_ENDPOINT}/0"
CACHE_EXPIRY = 5 * 60 * 60

# Temporarily disabling until billing issues with AWS are settled.
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': CACHE_LOCATION,
#         'OPTIONS': {
#             'REDIS_CLIENT_CLASS': 'rediscluster.RedisCluster',
#             'CONNECTION_POOL_CLASS': (
#                 'rediscluster.connection.ClusterConnectionPool'),
#             'CONNECTION_POOL_KWARGS': {
#                 # AWS ElastiCache has configuration commands disabled.
#                 'skip_full_coverage_check': True
#             }
#         }
#     }
# }
