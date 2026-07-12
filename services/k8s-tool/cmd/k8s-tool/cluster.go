package main

import (
	"context"
	"fmt"
	"strings"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
)

type clusterInspector struct {
	client kubernetes.Interface
}

func newClusterInspector() (kubernetesInspector, error) {
	config, err := rest.InClusterConfig()
	if err != nil {
		loadingRules := clientcmd.NewDefaultClientConfigLoadingRules()
		clientConfig := clientcmd.NewNonInteractiveDeferredLoadingClientConfig(
			loadingRules,
			&clientcmd.ConfigOverrides{},
		)
		config, err = clientConfig.ClientConfig()
		if err != nil {
			return nil, fmt.Errorf("build kubernetes config: %w", err)
		}
	}

	client, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, fmt.Errorf("create kubernetes client: %w", err)
	}
	return clusterInspector{client: client}, nil
}

func (inspector clusterInspector) ClusterHealth(
	ctx context.Context,
	namespace string,
) ([]workloadHealth, error) {
	if namespace == "" {
		deployments, err := inspector.client.AppsV1().Deployments("").List(ctx, metav1.ListOptions{})
		if err != nil {
			return nil, err
		}
		return deploymentHealthList(deployments.Items), nil
	}

	deployments, err := inspector.client.AppsV1().Deployments(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, err
	}
	return deploymentHealthList(deployments.Items), nil
}

func (inspector clusterInspector) DeploymentDiagnosis(
	ctx context.Context,
	namespace string,
	name string,
) (deploymentDiagnosisResponse, bool, error) {
	deployment, err := inspector.client.AppsV1().Deployments(namespace).Get(
		ctx,
		name,
		metav1.GetOptions{},
	)
	if err != nil {
		return deploymentDiagnosisResponse{}, false, nil
	}

	selector := labelsFromMatchLabels(deployment.Spec.Selector.MatchLabels)
	pods, err := inspector.client.CoreV1().Pods(namespace).List(
		ctx,
		metav1.ListOptions{LabelSelector: selector},
	)
	if err != nil {
		return deploymentDiagnosisResponse{}, false, err
	}
	events, err := inspector.client.CoreV1().Events(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return deploymentDiagnosisResponse{}, false, err
	}

	podStatuses := podStatusList(pods.Items)
	eventStatuses := eventListForDeployment(events.Items, name)
	logs := inspector.logExcerpts(ctx, namespace, pods.Items)
	health := deploymentHealth(*deployment)
	return deploymentDiagnosisResponse{
		Namespace:       namespace,
		Name:            name,
		Health:          health,
		Pods:            podStatuses,
		Events:          eventStatuses,
		Logs:            logs,
		Recommendations: recommendations(health, podStatuses, eventStatuses, logs),
	}, true, nil
}

func (inspector clusterInspector) logExcerpts(
	ctx context.Context,
	namespace string,
	pods []corev1.Pod,
) []containerLog {
	logs := make([]containerLog, 0)
	tailLines := int64(25)
	for _, pod := range pods {
		for _, container := range pod.Spec.Containers {
			text, err := inspector.client.CoreV1().Pods(namespace).GetLogs(
				pod.Name,
				&corev1.PodLogOptions{
					Container: container.Name,
					TailLines: &tailLines,
				},
			).DoRaw(ctx)
			if err == nil && len(text) > 0 {
				logs = append(logs, containerLog{
					Namespace:     namespace,
					PodName:       pod.Name,
					ContainerName: container.Name,
					Text:          string(text),
				})
			}
		}
	}
	return logs
}

func deploymentHealthList(deployments []appsv1.Deployment) []workloadHealth {
	workloads := make([]workloadHealth, 0, len(deployments))
	for _, deployment := range deployments {
		workloads = append(workloads, deploymentHealth(deployment))
	}
	return workloads
}

func deploymentHealth(deployment appsv1.Deployment) workloadHealth {
	desired := int(deployment.Status.Replicas)
	if deployment.Spec.Replicas != nil {
		desired = int(*deployment.Spec.Replicas)
	}
	ready := int(deployment.Status.ReadyReplicas)
	unavailable := desired - ready
	status := "Healthy"
	reason := "All replicas are ready"
	if unavailable > 0 {
		status = "Degraded"
		reason = fmt.Sprintf("%d replicas unavailable", unavailable)
	}
	return workloadHealth{
		Namespace:       deployment.Namespace,
		Name:            deployment.Name,
		Kind:            "Deployment",
		DesiredReplicas: desired,
		ReadyReplicas:   ready,
		Status:          status,
		Reason:          reason,
	}
}

func podStatusList(pods []corev1.Pod) []podStatus {
	statuses := make([]podStatus, 0, len(pods))
	for _, pod := range pods {
		restarts := 0
		ready := len(pod.Status.ContainerStatuses) > 0
		var reason *string
		for _, containerStatus := range pod.Status.ContainerStatuses {
			restarts += int(containerStatus.RestartCount)
			ready = ready && containerStatus.Ready
			if containerStatus.State.Waiting != nil && containerStatus.State.Waiting.Reason != "" {
				waitingReason := containerStatus.State.Waiting.Reason
				reason = &waitingReason
			}
		}
		phase := string(pod.Status.Phase)
		statuses = append(statuses, podStatus{
			Namespace:    pod.Namespace,
			Name:         pod.Name,
			Phase:        phase,
			Ready:        ready,
			RestartCount: restarts,
			Reason:       reason,
		})
	}
	return statuses
}

func eventListForDeployment(events []corev1.Event, deploymentName string) []kubernetesEvent {
	results := make([]kubernetesEvent, 0)
	for _, event := range events {
		if !strings.Contains(event.InvolvedObject.Name, deploymentName) {
			continue
		}
		results = append(results, kubernetesEvent{
			Namespace:      event.Namespace,
			InvolvedObject: event.InvolvedObject.Name,
			Reason:         event.Reason,
			Message:        event.Message,
			EventType:      event.Type,
		})
	}
	return results
}

func labelsFromMatchLabels(labels map[string]string) string {
	parts := make([]string, 0, len(labels))
	for key, value := range labels {
		parts = append(parts, fmt.Sprintf("%s=%s", key, value))
	}
	return strings.Join(parts, ",")
}

func recommendations(
	health workloadHealth,
	pods []podStatus,
	events []kubernetesEvent,
	logs []containerLog,
) []string {
	results := make([]string, 0)
	for _, pod := range pods {
		if pod.Reason == nil {
			continue
		}
		if *pod.Reason == "ImagePullBackOff" {
			results = append(results, "Verify the image name, tag, registry credentials, and pull secret.")
		}
		if *pod.Reason == "CrashLoopBackOff" {
			results = append(results, "Inspect previous container logs and recent configuration changes.")
		}
	}
	if strings.Contains(strings.ToLower(health.Reason), "readiness") {
		results = append(results, "Check readiness probe path, port, timeout, and application startup logs.")
	}
	for _, log := range logs {
		text := strings.ToLower(log.Text)
		if strings.Contains(text, "missing") && strings.Contains(text, "environment variable") {
			results = append(results, "Compare required environment variables against the deployment manifest.")
			break
		}
	}
	if len(events) > 0 && len(results) == 0 {
		results = append(results, "Inspect warning events and recent deployment changes.")
	}
	if len(results) == 0 {
		results = append(results, "Inspect rollout status, pod events, and recent deployment changes.")
	}
	return results
}
