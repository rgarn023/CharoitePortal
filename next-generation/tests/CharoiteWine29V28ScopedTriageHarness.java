package com.charoitegames.core;

/** CI-only synthetic fixture test; never accesses actual V28 or starts Wine. */
public final class CharoiteWine29V28ScopedTriageHarness {
    private static String summarize(String scm,String helper){
        StringBuilder b=new StringBuilder();
        CharoiteWine29V28ScopedTriage.appendMarkers(b,scm,helper);
        return b.toString();
    }
    private static void require(boolean ok,String reason){
        if(!ok)throw new AssertionError(reason);
    }
    private static void has(String out,String expected){
        require(out.contains(expected),"Missing fixed output: "+expected);
    }
    private static void lacks(String out,String forbidden){
        require(!out.contains(forbidden),"Leaked synthetic raw text: "+forbidden);
    }
    public static void main(String[] unused){
        String running=summarize(
            "SERVICE_NAME: RpcSs\n" +
            "        TYPE               : 20  WIN32_SHARE_PROCESS\n" +
            "        STATE              : 4  RUNNING\n" +
            "        WIN32_EXIT_CODE    : 0  (0x0)\n",
            "trace:setupapi:start\nerr:setupapi:CreateService failed: no such service\n" +
            "err:setupapi:SomePrivatePath secret.txt unknown warning\n");
        has(running,"scoped STATE: RUNNING");
        has(running,"scoped STATE code: 4");
        has(running,"single anchored state row: true");
        has(running,"service creation failure: true");
        has(running,"unclassified error line count (capped 999+): 1");
        lacks(running,"secret.txt");
        lacks(running,"SomePrivatePath");
        String stopped=summarize("SERVICE_NAME: RpcSs\n STATE : 1 STOPPED\n",null);
        has(stopped,"scoped STATE: STOPPED");
        has(stopped,"scoped STATE code: 1");
        has(stopped,"error lines: UNKNOWN (no eligible log)");
        String nameOnly=summarize(
            "notice: service_name: rpcss\n debug: STATE : 4 RUNNING\n", "");
        has(nameOnly,"scoped STATE: UNKNOWN / AMBIGUOUS");
        String other=summarize(
            "SERVICE_NAME: OtherService\n STATE : 4 RUNNING\n"
            +"SERVICE_NAME: RpcSs\n STATE : 1 STOPPED\n", "");
        has(other,"scoped STATE: STOPPED");
        has(other,"other service block observed: true");
        String mismatch=summarize("SERVICE_NAME: RpcSs\n STATE : 4 STOPPED\n", "");
        has(mismatch,"scoped STATE: UNKNOWN / AMBIGUOUS");
        String duplicate=summarize(
            "SERVICE_NAME: RpcSs\n STATE : 4 RUNNING\n STATE : 1 STOPPED\n","");
        has(duplicate,"scoped STATE: UNKNOWN / AMBIGUOUS");
        String noState=summarize("SERVICE_NAME: RpcSs\n"
            +"trace:service: state\n", "");
        has(noState,"scoped STATE: UNKNOWN / AMBIGUOUS");
        String noLogs=summarize(null,null);
        has(noLogs,"scoped STATE: UNKNOWN (no eligible log)");
        has(noLogs,"error lines: UNKNOWN (no eligible log)");
        String section=summarize("SERVICE_NAME: RpcSs\n STATE : 2 START_PENDING\n",
            "err:setupapi:section missing\nerr:setupapi:access denied\n"
            +"err:setupapi:not implemented\nerr:setupapi:invalid parameter\n");
        has(section,"scoped STATE: START_PENDING");
        has(section,"missing INF section: true");
        has(section,"access denied: true");
        has(section,"unimplemented/stub: true");
        has(section,"invalid parameter: true");
        String stoppedNeverStarted=summarize(
            "SERVICE_NAME: RpcSs\n STATE : 1 STOPPED\n"
            + " WIN32_EXIT_CODE : 1077 (0x435)\n",
            "err:setupapi:failed to query value secretName, error 2\n"
            + "err:setupapi:failed to set value secretName, error 5\n"
            + "err:setupapi:could not create key 0xabcd secretName\n"
            + "err:setupapi:copy error 123 /private/path -> /other\n"
            + "err:setupapi:Unsupported style(s) 0x123\n");
        has(stoppedNeverStarted,"WIN32_EXIT_CODE class: SERVICE_NEVER_STARTED");
        has(stoppedNeverStarted,"registry value query error: true");
        has(stoppedNeverStarted,"registry value set error: true");
        has(stoppedNeverStarted,"registry key create error: true");
        has(stoppedNeverStarted,"file copy/rename error: true");
        has(stoppedNeverStarted,"unsupported file style: true");
        has(stoppedNeverStarted,"unclassified error line count (capped 999+): 0");
        lacks(stoppedNeverStarted,"secretName");
        lacks(stoppedNeverStarted,"/private/path");
        StringBuilder reg=new StringBuilder();
        CharoiteWine29V28ScopedTriage.appendRegistryStart(reg,
            "WINE REGISTRY VERSION 2\n"
            + "[System\\\\CurrentControlSet\\\\Services\\\\RpcSs]\n"
            + "\"Start\"=dword:00000003\n");
        has(reg.toString(),"RpcSs registry Start mode: DEMAND_START");
        reg.setLength(0);
        CharoiteWine29V28ScopedTriage.appendRegistryStart(reg,
            "[System\\\\CurrentControlSet\\\\Services\\\\RpcSs]\n"
            + "\"Start\"=dword:00000003\n"
            + "\"Start\"=dword:00000002\n");
        has(reg.toString(),"RpcSs registry Start mode: UNKNOWN / AMBIGUOUS");
        reg.setLength(0);
        CharoiteWine29V28ScopedTriage.appendRegistryStart(reg,null);
        has(reg.toString(),"RpcSs registry Start mode: UNKNOWN (no eligible registry)");
        System.out.println("V28_SCOPED_SCM_STATE_AND_SETUPAPI_SYNTHETIC_JAVA_GATE=PASS");
    }
}
