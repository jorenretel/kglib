load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

def graknlabs_build_tools():
    git_repository(
        name = "graknlabs_build_tools",
        remote = "https://github.com/graknlabs/build-tools",
        commit = "b731eae85c90128878de58848a1cd8fe516ce58e", # sync-marker: do not remove this comment, this is used for sync-dependencies by @graknlabs_build_tools
    )


def graknlabs_grakn_core():
    git_repository(
        name = "graknlabs_grakn_core",
        remote = "https://github.com/graknlabs/grakn",
        tag = "1.6.2"  # sync-marker: do not remove this comment, this is used for sync-dependencies by @graknlabs_grakn_core
    )

def graknlabs_client_python():
    git_repository(
        name = "graknlabs_client_python",
        remote = "https://github.com/graknlabs/client-python",
        tag = "1.6.0" # sync-marker: do not remove this comment, this is used for sync-dependencies by @graknlabs_client_python
    )
