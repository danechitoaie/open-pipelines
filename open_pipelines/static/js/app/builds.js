$(document).ready(function() {
    var $opBuild = $(".op__build");

    var stripANSIEscapeCodes = function(str) {
        var ansiRegex = /[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-PRZcf-nqry=><]/g;
        return typeof str === "string" ? str.replace(ansiRegex, "") : str;
    };

    var updateDatetime = function() {
        var $dateTime = $opBuild.find("div[data-datetime-start][data-datetime-elapsed]");
        if ($dateTime.length > 0) {
            var dtStart   = $dateTime.attr("data-datetime-start");
            var dtElapsed = $dateTime.attr("data-datetime-elapsed");

            if (dtStart !== "") {
                var timeStr = moment(dtStart, "YYYY-MM-DD HH:mm:ss ZZ").fromNow();

                if (dtElapsed !== "") {
                    timeStr += " (" +  dtElapsed  + ")";
                }

                $dateTime.find("> span").html(timeStr);
            }
        }
    };

    var processBuildStatus = function(r) {
        var $buildStatus = $opBuild.find(".op__build__status");

        if (r.build_status === "INPROGRESS") {
            if (!$buildStatus.hasClass("op__build__status__inprogress")) {
                $buildStatus.replaceWith($("#script-template-build-status-inprogress").html());
            }
            return;
        }

        if (r.build_status === "SUCCESSFUL") {
            if (!$buildStatus.hasClass("op__build__status__successful")) {
                $buildStatus.replaceWith($("#script-template-build-status-successful").html());
            }
            return;
        }

        if (r.build_status === "FAILED") {
            if (!$buildStatus.hasClass("op__build__status__failed")) {
                $buildStatus.replaceWith($("#script-template-build-status-failed").html());
            }
            return;
        }

        if (!$buildStatus.hasClass("op__build__status__unknown")) {
            $buildStatus.replaceWith($("#script-template-build-status-unknown").html());
        }
    };

    var processTimestamp = function(r) {
        var $dateTime = $opBuild.find("div[data-datetime-start][data-datetime-elapsed]");
        if (r.build_datetime_start !== null) {
            $dateTime.attr("data-datetime-start", r.build_datetime_start);
        }

        if (r.build_datetime_elapsed !== null) {
            $dateTime.attr("data-datetime-elapsed", r.build_datetime_elapsed);
        }
    };

    var processDockerImage = function(r) {
        var $dockerImage = $opBuild.find("div[data-docker-image]");
        if (r.build_docker_image !== null) {
            $dockerImage.find("> span").html(r.build_docker_image);
        }
    };

    var updateBuildProgress = function(codeMirror, buildUrl) {
        return function() {
            $.get(buildUrl, function(r) {
                if (r.status === "ok") {
                    processBuildStatus(r);
                    processTimestamp(r);
                    processDockerImage(r);

                    if (r.build_output.length > 0) {
                        codeMirror.replaceRange(stripANSIEscapeCodes(r.build_output), {line: Infinity});
                        codeMirror.execCommand("goDocEnd");
                    }

                    if (r.build_status === "INPROGRESS" && r.build_url_more !== null) {
                        setTimeout(updateBuildProgress(codeMirror, r.build_url_more), 1000);
                    }

                    return;
                }

                var compileTemplate = _.template($("#script-template-error").html());
                var $domElement     = $opBuild.find("> .column .op__build__logs > .ui.stacked.segment");
                $domElement.html(compileTemplate({
                    "message" : "Error retrieving data about the current build!"
                }));
            }).fail(function(xhr) {
                var compileTemplate = _.template($("#script-template-error").html());
                var $domElement     = $opBuild.find("> .column .op__build__logs > .ui.stacked.segment");
                $domElement.html(compileTemplate({
                    "message" : "Error retrieving data about the current build!"
                }));
            });
        };
    };

    if ($opBuild.length > 0) {
        var buildUrl = $opBuild.attr("data-build-url");

        $.get(buildUrl, function(r) {
            if (r.status === "ok") {
                processBuildStatus(r);
                processTimestamp(r);
                processDockerImage(r);

                updateDatetime();
                setInterval(updateDatetime, 1000);

                var $domElement = $opBuild.find("> .column .op__build__logs > .ui.stacked.segment");
                $domElement.empty();

                var codeMirror = CodeMirror($domElement.get(0), {
                    value        : stripANSIEscapeCodes(r.build_output),
                    mode         : "shell",
                    lineNumbers  : true,
                    lineWrapping : true,
                    readOnly     : true,
                });

                codeMirror.execCommand("goDocEnd");

                if (r.build_status === "INPROGRESS" && r.build_url_more !== null) {
                    setTimeout(updateBuildProgress(codeMirror, r.build_url_more), 1000);
                }

                return;
            }

            var compileTemplate = _.template($("#script-template-error").html());
            var $domElement     = $opBuild.find("> .column .op__build__logs > .ui.stacked.segment");
            $domElement.html(compileTemplate({
                "message" : "Error retrieving data about the current build!"
            }));
        }).fail(function(xhr) {
            var compileTemplate = _.template($("#script-template-error").html());
            var $domElement     = $opBuild.find("> .column .op__build__logs > .ui.stacked.segment");
            $domElement.html(compileTemplate({
                "message" : "Error retrieving data about the current build!"
            }));
        });
    }
});