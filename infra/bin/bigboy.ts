#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { BigboyStack } from '../lib/bigboy-stack';

const app = new cdk.App();

new BigboyStack(app, 'BigboyStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'bigboy: VPC, RDS Postgres, ECS Fargate (Django+ALB, LangGraph+Cloud Map), CloudFront, Amplify',
});

app.synth();
