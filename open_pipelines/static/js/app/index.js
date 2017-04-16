$(document).ready(function() {
    var open_pipelines_yml = "";
    open_pipelines_yml += "# This is a sample build configuration for Javascript (Node.js).\n";
    open_pipelines_yml += "# Only use spaces to indent your .yml configuration.\n";
    open_pipelines_yml += "# -----\n";
    open_pipelines_yml += "# You can specify a custom docker image from Docker Hub as your build environment.\n";
    open_pipelines_yml += "image: node:latest\n";
    open_pipelines_yml += "\n";
    open_pipelines_yml += "pipeline:\n";
    open_pipelines_yml += "    - node --version\n";

    var $requestUrl = $(".op__repos__content table[data-request-url]");
    if ($requestUrl.length > 0) {
        var requestUrl = $requestUrl.attr("data-request-url");
        $.get(requestUrl, function(r) {
            if (r.status === "ok") {
                var compileTemplate = _.template($("#script-template-repos").html());
                $(".op__repos__content").html(compileTemplate(r.data));
                return;
            }

            var compileTemplate = _.template($("#script-template-error").html());
            $(".op__repos__content").html(compileTemplate({
                "message" : "Failed to retrieve the list of Git repos!"
            }));
        }).fail(function(xhr) {
            if (xhr.status === 401) {
                var compileTemplate = _.template($("#script-template-error").html());
                $(".op__repos__content").find("> .content").html(compileTemplate({
                    "message" : "Unauthorized! Please login to access this data!"
                }));
                return;
            }

            var compileTemplate = _.template($("#script-template-error").html());
            $(".op__repos__content").html(compileTemplate({
                "message" : "Failed to retrieve the list of Git repos!"
            }));
        });
    }

    /* Prev/Next */
    $(document).on("click", ".op__repos__content table tfoot .pagination a:not(.disabled)", function(e) {
        e.preventDefault();

        var compileTemplate = _.template($("#script-template-loader").html());
        $(".op__repos__content").prepend(compileTemplate());

        var requestUrl = $(this).attr("href");
        $.get(requestUrl, function(r) {
            if (r.status === "ok") {
                var compileTemplate = _.template($("#script-template-repos").html());
                $(".op__repos__content").html(compileTemplate(r.data));
                return;
            }

            var compileTemplate = _.template($("#script-template-error").html());
            $(".op__repos__content").html(compileTemplate({
                "message" : "Failed to retrieve the list of Git repos!"
            }));
        }).fail(function(xhr) {
            if (xhr.status === 401) {
                var compileTemplate = _.template($("#script-template-error").html());
                $(".op__repos__content").find("> .content").html(compileTemplate({
                    "message" : "Unauthorized! Please login to access this data!"
                }));
                return;
            }

            var compileTemplate = _.template($("#script-template-error").html());
            $(".op__repos__content").html(compileTemplate({
                "message" : "Failed to retrieve the list of Git repos!"
            }));
        });
    });

    /* Configure */
    function enable_onChange($modal, repoPath, repoName, repoUrl) {
        return function() {
            $modal.find("> .content").prepend(
                $("#script-template-loader").html()
            );

            var $checkbox = $modal.find("> .content table tfoot .ui.toggle.checkbox");
            var isEnabled = $checkbox.checkbox("is checked");
            var reqMethod = isEnabled ? "enable" : "disable";

            $.post(repoUrl, {"method" : reqMethod}, function(r) {
                if (r.status === "ok" && r.hasOwnProperty("enabled") && r.enabled === true) {
                    var compileTemplate = _.template($("#script-template-modal-enabled").html());
                    $modal.find("> .content").html(compileTemplate({
                        "webhook" : r.webhook
                    }));

                    var domObject  = $modal.find("> .content .open_pipelines_yml").get(0);
                    var codeMirror = CodeMirror(domObject, {
                        value       : open_pipelines_yml,
                        mode        : "yaml",
                        lineNumbers : true,
                        readOnly    : true,
                    });

                    var publicState = r.public ? "check" : "uncheck";
                    $modal.find("> .content table tbody .ui.checkbox").checkbox(publicState).checkbox({
                        onChange : public_onChange($modal, repoPath, repoName, repoUrl)
                    });

                    var enabledState = r.enabled ? "check" : "uncheck";
                    $modal.find("> .content table tfoot .ui.toggle.checkbox").checkbox(enabledState).checkbox({
                        onChange : enable_onChange($modal, repoPath, repoName, repoUrl)
                    });

                    $(".repo__status[data-repo-path='" + repoPath + "'] > i").removeClass("grey radio").addClass("green check circle outline");
                    return;
                }

                if (r.status === "ok" && r.hasOwnProperty("enabled") && r.enabled === false) {
                    $modal.find("> .content").html(
                        $("#script-template-modal-disabled").html()
                    );

                    var publicState = r.public ? "check" : "uncheck";
                    $modal.find("> .content table tbody .ui.checkbox").checkbox(publicState).checkbox({
                        onChange : public_onChange($modal, repoPath, repoName, repoUrl)
                    });

                    var enabledState = r.enabled ? "check" : "uncheck";
                    $modal.find("> .content table tfoot .ui.toggle.checkbox").checkbox(enabledState).checkbox({
                        onChange : enable_onChange($modal, repoPath, repoName, repoUrl)
                    });

                    $(".repo__status[data-repo-path='" + repoPath + "'] > i").removeClass("green check circle outline").addClass("grey radio");
                    return;
                }

                var compileTemplate = _.template($("#script-template-error").html());
                $modal.find("> .content").html(compileTemplate({
                    "message" : "Failed to update selected repo!"
                }));
            }).fail(function(xhr) {
                if (xhr.status === 401) {
                    var compileTemplate = _.template($("#script-template-error").html());
                    $modal.find("> .content").html(compileTemplate({
                        "message" : "Unauthorized! Please login to access this data!"
                    }));
                    return;
                }

                var compileTemplate = _.template($("#script-template-error").html());
                $modal.find("> .content").html(compileTemplate({
                    "message" : "Failed to update selected repo!"
                }));
            });
        };
    }

    function public_onChange($modal, repoPath, repoName, repoUrl) {
        return function() {
            var $checkbox = $modal.find("> .content table tbody .ui.checkbox");
            var isEnabled = $checkbox.checkbox("is checked");
            var reqMethod = isEnabled ? "public" : "private";

            $.post(repoUrl, {"method" : reqMethod}, function(r) {
                if (r.status === "ok") {
                    var publicState = r.public ? "check" : "uncheck";
                    $modal.find("> .content table tbody .ui.checkbox").checkbox(publicState);
                    return;
                }

                var compileTemplate = _.template($("#script-template-error").html());
                $modal.find("> .content").html(compileTemplate({
                    "message" : "Failed to update selected repo!"
                }));
            }).fail(function(xhr) {
                if (xhr.status === 401) {
                    var compileTemplate = _.template($("#script-template-error").html());
                    $modal.find("> .content").html(compileTemplate({
                        "message" : "Unauthorized! Please login to access this data!"
                    }));
                    return;
                }

                var compileTemplate = _.template($("#script-template-error").html());
                $modal.find("> .content").html(compileTemplate({
                    "message" : "Failed to update selected repo!"
                }));
            });
        };
    }

    $(document).on("click", ".op__repos__content table tbody td.right.aligned button", function(e) {
        e.preventDefault();

        var $this    = $(this);
        var repoPath = $this.attr("data-repo-path");
        var repoName = $this.attr("data-repo-name");
        var repoUrl  = $this.attr("data-repo-url");

        $('.op__repos__modal.ui.modal').modal({
            closable: false,
            observeChanges: true,
            onShow: function() {
                var $modal = $(this);
                $modal.find("> .header").html(repoName);

                var compileTemplate = _.template($("#script-template-modal-loading").html());
                $modal.find("> .content").html(compileTemplate());
            },
            onVisible: function() {
                var $modal = $(this);

                $.get(repoUrl, function(r) {
                    if (r.status === "ok") {
                        var compileTemplate = _.template($("#script-template-modal-enabled").html());
                        $modal.find("> .content").html(compileTemplate({
                            "webhook" : r.webhook
                        }));

                        var domObject  = $modal.find("> .content .open_pipelines_yml").get(0);
                        var codeMirror = CodeMirror(domObject, {
                            value       : open_pipelines_yml,
                            mode        : "yaml",
                            lineNumbers : true,
                            readOnly    : true,
                        });

                        var publicState = r.public ? "check" : "uncheck";
                        $modal.find("> .content table tbody .ui.checkbox").checkbox(publicState).checkbox({
                            onChange : public_onChange($modal, repoPath, repoName, repoUrl)
                        });

                        var enabledState = r.enabled ? "check" : "uncheck";
                        $modal.find("> .content table tfoot .ui.toggle.checkbox").checkbox(enabledState).checkbox({
                            onChange : enable_onChange($modal, repoPath, repoName, repoUrl)
                        });
                        return;
                    }

                    var compileTemplate = _.template($("#script-template-error").html());
                    $modal.find("> .content").html(compileTemplate({
                        "message" : "Failed to retrieve data about selected repo!"
                    }));
                }).fail(function(xhr) {
                    if (xhr.status === 401) {
                        var compileTemplate = _.template($("#script-template-error").html());
                        $modal.find("> .content").html(compileTemplate({
                            "message" : "Unauthorized! Please login to access this data!"
                        }));
                        return;
                    }

                    if (xhr.status === 404) {
                        $modal.find("> .content").html(
                            $("#script-template-modal-disabled").html()
                        );

                        var publicState = "uncheck";
                        $modal.find("> .content table tbody .ui.checkbox").checkbox(publicState).checkbox({
                            onChange : public_onChange($modal, repoPath, repoName, repoUrl)
                        });

                        var enabledState = "uncheck";
                        $modal.find("> .content table tfoot .ui.toggle.checkbox").checkbox(enabledState).checkbox({
                            onChange : enable_onChange($modal, repoPath, repoName, repoUrl)
                        });
                        return;
                    }

                    var compileTemplate = _.template($("#script-template-error").html());
                    $modal.find("> .content").html(compileTemplate({
                        "message" : "Failed to retrieve data about selected repo!"
                    }));
                });
            }
        }).modal('show');
    });
});