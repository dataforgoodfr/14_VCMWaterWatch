# Coolify

 - Coolify is set up under /data/coolify on vcm-watch.eu
 - Connect to https://coolify.vcm-watch.eu to manage
 - Everything runs under docker compose, using the docker-compose.deploy.yml file at the root of the repo

## Deployment Hooks

 - Runs from github action -> pushes to main will trigger a build, push the image, and tell coolify to redeploy
 - Configure under Project > Webhooks in Coolify

## Notifications

 - Configure under Notifications in Coolify, currently using Resend

## Resources

 - Postgres database configured in Coolify resources, with daily backups

## Test Environment

 - HEADS UP: this is not completely set up, we should have different images or a way to pull a specific tag,
 right now the prod and test images are the same so it's possible for a test push to interfere with the
 production deployment!  Use with caution!
 - nocodb-test.vcm-watch.eu / test.vcm-watch.eu
 - configure a branch to test under the setting, but you'll have to manually trigger the workflow in github
 to push an image

