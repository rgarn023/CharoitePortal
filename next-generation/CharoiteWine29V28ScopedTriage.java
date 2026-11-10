package com.charoitegames.core;

import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Pure string classifier for the ALREADY BOUNDED, owner-authorized V28
 * read-only evidence. No file/network/exec/Android APIs, no raw log output.
 *
 * Scope SCM state to one exact RpcSs SERVICE_NAME block and one anchored
 * STATE row. A generic occurrence of "state" is NOT sufficient.
 */
public final class CharoiteWine29V28ScopedTriage {
    private static final Pattern SERVICE = Pattern.compile(
        "^\\s*service_name\\s*:\\s*([^\\s]+)\\s*$", Pattern.CASE_INSENSITIVE);
    private static final Pattern STATE = Pattern.compile(
        "^\\s*state\\s*:\\s*([0-9]+)(?:\\s+([a-z_]+))?(?:\\s+.*)?$",
        Pattern.CASE_INSENSITIVE);
    private static final String[] STATES = {
        "UNKNOWN", "STOPPED", "START_PENDING", "STOP_PENDING", "RUNNING",
        "CONTINUE_PENDING", "PAUSE_PENDING", "PAUSED"
    };
    private CharoiteWine29V28ScopedTriage() {}

    private static String stateLabel(int code) {
        return code>=1 && code<=7 ? STATES[code] : "UNKNOWN";
    }

    private static void classifyScm(StringBuilder out, String scm) {
        if(scm==null || scm.length()>2097152){
            out.append("V28 preserved RpcSs SCM scoped STATE: UNKNOWN (no eligible log)\n");
            out.append("V28 preserved RpcSs SCM single anchored state row: false\n");
            out.append("V28 preserved RpcSs SCM status is HISTORICAL, never a live-service check\n");
            return;
        }
        int headers=0, rows=0, stateCode=-1;
        boolean inside=false,validLabel=true,otherService=false;
        for(String line:scm.split("\n",-1)){
            Matcher header=SERVICE.matcher(line);
            if(header.matches()){
                inside="rpcss".equalsIgnoreCase(header.group(1));
                if(inside)headers++;
                else otherService=true;
                continue;
            }
            if(!inside)continue;
            Matcher state=STATE.matcher(line);
            if(!state.matches())continue;
            rows++;
            int code;
            try{code=Integer.parseInt(state.group(1));}
            catch(NumberFormatException ignored){code=-1;}
            String expected=stateLabel(code);
            String actual=state.group(2);
            if(!"UNKNOWN".equals(expected)
                    && (actual==null || expected.equalsIgnoreCase(actual))
                    && stateCode<0){
                stateCode=code;
            }else{
                validLabel=false;
            }
        }
        boolean single=(headers==1 && rows==1 && validLabel && stateCode>=1);
        out.append("V28 preserved RpcSs SCM exact service header count: ")
           .append(headers>=2?"2+":"0".equals(Integer.toString(headers))?"0":"1").append('\n');
        out.append("V28 preserved RpcSs SCM other service block observed: ")
           .append(otherService).append('\n');
        out.append("V28 preserved RpcSs SCM single anchored state row: ")
           .append(single).append('\n');
        out.append("V28 preserved RpcSs SCM scoped STATE: ")
           .append(single?stateLabel(stateCode):"UNKNOWN / AMBIGUOUS").append('\n');
        out.append("V28 preserved RpcSs SCM scoped STATE code: ")
           .append(single?Integer.toString(stateCode):"UNKNOWN").append('\n');
        out.append("V28 preserved RpcSs SCM status is HISTORICAL, never a live-service check\n");
    }

    private static void classifySetupApi(StringBuilder out, String helper) {
        if(helper==null || helper.length()>4194304){
            out.append("V28 preserved SetupAPI error lines: UNKNOWN (no eligible log)\n");
            return;
        }
        int count=0,uncategorized=0;
        boolean missingInf=false,missingSection=false,serviceFailure=false,
                notImplemented=false,accessDenied=false,invalidParameter=false;
        for(String text:helper.split("\n",-1)){
            String line=text.toLowerCase(Locale.US);
            if(!line.contains("err:setupapi:"))continue;
            count++;
            boolean classified=false;
            if(line.contains("failed to open") || line.contains("cannot open")
                    || line.contains("file not found") || line.contains("no such file")){
                missingInf=true;classified=true;
            }
            if(line.contains("section") && (line.contains("not found")
                    || line.contains("missing") || line.contains("unknown"))){
                missingSection=true;classified=true;
            }
            if(line.contains("service") && (line.contains("fail")
                    || line.contains("error") || line.contains("could not"))){
                serviceFailure=true;classified=true;
            }
            if(line.contains("not implemented") || line.contains("unimplemented")
                    || line.contains("stub")){
                notImplemented=true;classified=true;
            }
            if(line.contains("access denied")){accessDenied=true;classified=true;}
            if(line.contains("invalid parameter")){invalidParameter=true;classified=true;}
            if(!classified)uncategorized++;
        }
        out.append("V28 preserved SetupAPI error lines (capped 999+): ")
           .append(count>999?"999+":Integer.toString(count)).append('\n');
        out.append("V28 preserved SetupAPI error category: INF/file-open failure: ")
           .append(missingInf).append('\n');
        out.append("V28 preserved SetupAPI error category: missing INF section: ")
           .append(missingSection).append('\n');
        out.append("V28 preserved SetupAPI error category: service creation failure: ")
           .append(serviceFailure).append('\n');
        out.append("V28 preserved SetupAPI error category: unimplemented/stub: ")
           .append(notImplemented).append('\n');
        out.append("V28 preserved SetupAPI error category: access denied: ")
           .append(accessDenied).append('\n');
        out.append("V28 preserved SetupAPI error category: invalid parameter: ")
           .append(invalidParameter).append('\n');
        out.append("V28 preserved SetupAPI unclassified error line count (capped 999+): ")
           .append(uncategorized>999?"999+":Integer.toString(uncategorized)).append('\n');
        out.append("SetupAPI error markers alone are NOT proof of installation failure\n");
    }

    public static void appendMarkers(StringBuilder out, String scm, String helper) {
        classifyScm(out,scm);
        classifySetupApi(out,helper);
    }
}
