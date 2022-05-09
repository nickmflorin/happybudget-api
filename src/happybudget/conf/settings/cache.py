from happybudget.conf import config, Environments

# Temporarily disabling due to cost of operation.
CACHE_ENABLED = False
CACHE_EXPIRY = 5 * 60 * 60

ELASTICACHE_ENDPOINT = config(
    name='ELASTICACHE_ENDPOINT',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: '',
        Environments.LOCAL: ''
    },
    enabled=CACHE_ENABLED
)

if CACHE_ENABLED:
    CACHE_LOCATION = f"redis://{ELASTICACHE_ENDPOINT}/0"
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': CACHE_LOCATION,
            'OPTIONS': {
                'REDIS_CLIENT_CLASS': 'rediscluster.RedisCluster',
                'CONNECTION_POOL_CLASS': (
                    'rediscluster.connection.ClusterConnectionPool'),
                'CONNECTION_POOL_KWARGS': {
                    # AWS ElastiCache has configuration commands disabled.
                    'skip_full_coverage_check': True
                }
            }
        }
    }
